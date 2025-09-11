from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, session
import redis
import mysql.connector
import time
import json

app = Flask(__name__)
app.secret_key = 'tvoj_tajni_ključ'

r = redis.Redis(host='localhost', port=6379, db=0)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="dbubanj",
        database="hotelmatch"
    )

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        user_key = f"user:{email}"
        fail_key = f"fail:{email}"
        conn = get_db_connection()
        
        if not r.exists(user_key):
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if not user:
                flash("Korisnik ne postoji. Molimo registrirajte se.", "danger")
                return redirect(url_for('login'))

            r.set(user_key, user[0], ex=1800)

        stored_password = r.get(user_key).decode()
        
        if password == stored_password:
            r.delete(fail_key)
            session["user_email"] = email
            return redirect(url_for('dashboard'))
        else:
            fails = r.incr(fail_key)
            if fails >= 3:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE email = %s", (email,))
                conn.commit()
                cursor.close()

                r.delete(user_key)
                r.delete(fail_key)

                flash("Previše neuspješnih pokušaja. Korisnik obrisan.", "danger")
                return redirect(url_for('register'))
            else:
                flash(f"Pogrešna lozinka. Pokušaj {fails} od 3.", "warning")
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email i lozinka su obavezni.", "danger")
            return redirect(url_for('register'))

        if r.exists(f"user:{email}"):
            flash("Korisnik već postoji (Redis)!", "danger")
            return redirect(url_for('register'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        cursor.close()

        if existing_user:
            conn.close()
            flash("Korisnik već postoji (MySQL)!", "danger")
            return redirect(url_for('register'))

        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        conn.commit()
        cursor.close()
        conn.close()

        r.set(f"user:{email}", password, ex=600)

        flash("Registracija uspješna!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/redis_data')
def redis_data():
    all_keys = r.keys('user:*')
    users = []
    for key in all_keys:
        email = key.decode().split("user:")[1]
        password = r.get(key).decode()

        fail_key = f"fail:{email}"
        fail_attempts = r.get(fail_key)
        fail_attempts = int(fail_attempts.decode()) if fail_attempts else 0

        users.append({
            'email': email,
            'password': password,
            'fail_attempts': fail_attempts
        })

    return render_template('redis_data.html', users=users)


def get_hotels_by_location(location, offset=0, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT HotelName, cityName, countyName, HotelRating, Address, HotelCode
        FROM hotels
        WHERE cityName LIKE %s OR countyName LIKE %s
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, ('%' + location + '%', '%' + location + '%', limit, offset))
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()
    return hotels


def get_total_hotels(location):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT COUNT(*) FROM hotels
        WHERE cityName LIKE %s OR countyName LIKE %s
    """
    cursor.execute(query, ('%' + location + '%', '%' + location + '%'))
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total


@app.route("/hoteli", methods=["GET"])
def prikaz_hotela():
    user_email = session.get("user_email")
    user_name = user_email.split("@")[0] if user_email else ""

    location = request.args.get("location", "")
    offset = int(request.args.get("offset", 0))
    limit = 20

    hotels = get_hotels_by_location(location, offset=offset, limit=limit) if location else []
    total_hotels = get_total_hotels(location) if location else 0
    start_num = offset + 1 if total_hotels > 0 else 0
    end_num = min(offset + limit, total_hotels)

    return render_template(
        "hotels_table.html",
        hotels=hotels,
        location=location,
        offset=offset,
        user_email=user_name,
        limit=limit,
        total_hotels=total_hotels,
        start_num=start_num,
        end_num=end_num
    )


def get_hotels_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT HotelName, Address, Map, HotelCode FROM hotels WHERE countyName IN (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", ('Croatia', 'Hungary', 'Italy', 'Ireland(Republic of)', 'Sweden', 'Finland', 'Estonia', 'Latvia', 'Lithuania', 'Denmark', 'Portugal', 'Spain', 'France', 'Germany','Slovakia', 'Slovenia', 'Austria', 'Romania', 'Greece', 'Cyprus', 'Bulgaria', 'Malta', 'Belgium', 'Luxembourg', 'Netherlands', 'Poland','Czech Republic'))
    hotels = cursor.fetchall()  
    cursor.close()
    conn.close()
    return hotels


@app.route('/hotels_map')
def hotels_map():
    start_time = time.time()
    hotels = get_hotels_from_db()
    end_time = time.time()  
    duration = end_time - start_time

    print(f"[INFO] Vrijeme potrebno za dohvat i prikaz hotela na karti: {duration:.2f} sekundi")

    return render_template('hotels_map.html', hotels=hotels)


@app.route('/hotel/<int:hotel_code>')
def hotel_detail(hotel_code):
    
    user_email = session.get("user_email")
    user_name = user_email.split("@")[0] if user_email else ""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hotels WHERE HotelCode = %s", (hotel_code,))
    hotel = cursor.fetchone()
    cursor.close()
    conn.close()

    if hotel:
        return render_template("hotel_details.html", hotel=hotel, user_email = user_name)
    else:
        return "Hotel nije pronađen", 404


def file_size(file):
    data_size = len(file)
    if data_size < 1024:
        size_str = f"{data_size} B"
    elif data_size < 1024**2:
        size_str = f"{data_size/1024:.2f} KB"
    else:
        size_str = f"{data_size/(1024**2):.2f} MB"
    return size_str


@app.route('/statistika')
def statistika():
    start_time = time.time() 

    cache_key = "stats:all"

    if r.exists(cache_key):
        print("[CACHE] Podaci dohvaćeni iz Redis-a")
        data = json.loads(r.get(cache_key))
        zupanije = data['zupanije']
        ocjene = data['ocjene']
        zvjezdice = data['zvjezdice']
        source = "Redis cache"
    else:
        print("[SQL] Podaci dohvaćeni iz MySQL-a")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT countyName, COUNT(*) AS broj FROM hotels GROUP BY countyName")
        zupanije = cursor.fetchall()

        cursor.execute("SELECT cityName, AVG(HotelRating) AS prosjek FROM hotels GROUP BY cityName")
        ocjene = cursor.fetchall()

        cursor.execute("SELECT HotelRating, COUNT(*) AS broj FROM hotels GROUP BY HotelRating")
        zvjezdice = cursor.fetchall()

        cursor.close()
        conn.close()
        
        data_json = json.dumps({
            "zupanije": zupanije,
            "ocjene": ocjene,
            "zvjezdice": zvjezdice
        })
        
        size_str = file_size(data_json.encode("utf-8"))

        r.set(cache_key, data_json, ex=600)

        source = "MySQL baza"

        print(f"[INFO] Veličina podataka: {size_str}")
    duration = time.time() - start_time  
    print(f"[INFO] Trajanje upita /statistika: {duration:.4f} sekundi.")

    return render_template("statistic.html",
                           zupanije=zupanije,
                           ocjene=ocjene,
                           zvjezdice=zvjezdice,
                           source=source)


@app.route("/filter")
def filter_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT countyName FROM hotels WHERE countyName IS NOT NULL")
    counties = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return render_template("filter.html", counties=counties)


@app.route("/api/hotels")
def api_hotels():
    rating = request.args.get("rating")
    county = request.args.get("county")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT HotelName, Address, Map, HotelCode FROM hotels WHERE 1=1"
    params = []

    if rating:
        try:
            query += " AND HotelRating = %s"
            params.append(int(rating))
        except ValueError:
            pass 

    if county:
        query += " AND countyName = %s"
        params.append(county)

    cursor.execute(query, params)
    hotels = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(hotels)


@app.route('/dashboard')
def dashboard():
    start_time = time.time()
    user_email = session.get("user_email")
    user_name = user_email.split("@")[0] if user_email else ""

    cache_key = "dashboard:data"

    if r.exists(cache_key):
        print("[CACHE] Podaci dohvaćeni iz Redis-a")
        data = json.loads(r.get(cache_key))
        hotels = data['hotels']
        zupanije = data['zupanije']
        ocjene = data['ocjene']
        zvjezdice = data['zvjezdice']
        source = "Redis cache"
    else:
        print("[SQL] Podaci dohvaćeni iz MySQL-a")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT HotelName, Address, Map, HotelCode, countyName
            FROM hotels
            WHERE countyName IN (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            'Croatia', 'Hungary', 'Italy', 'Ireland(Republic of)', 'Sweden', 'Finland',
            'Estonia', 'Latvia', 'Lithuania', 'Denmark', 'Portugal', 'Spain', 'France',
            'Germany', 'Slovakia', 'Slovenia', 'Austria', 'Romania', 'Greece', 'Cyprus',
            'Bulgaria', 'Malta', 'Belgium', 'Luxembourg', 'Netherlands', 'Poland', 'Czech Republic'
        ))
        hotels = cursor.fetchall()

        cursor.execute("SELECT countyName, COUNT(*) AS broj FROM hotels GROUP BY countyName")
        zupanije = cursor.fetchall()

        cursor.execute("SELECT countyName, AVG(HotelRating) AS prosjek FROM hotels GROUP BY countyName")
        ocjene = cursor.fetchall()

        cursor.execute("SELECT HotelRating, COUNT(*) AS broj FROM hotels GROUP BY HotelRating")
        zvjezdice = cursor.fetchall()

        cursor.close()
        conn.close()

        data = {
            'hotels': hotels,
            'zupanije': zupanije,
            'ocjene': ocjene,
            'zvjezdice': zvjezdice
        }
        data_json = json.dumps(data)
        
        size_str = file_size(data_json.encode("utf-8"))

        r.set(cache_key, json.dumps(data, default=str), ex=1800) 
        source = "MySQL baza"
        print(f"Veličina podataka: {size_str}")
    duration = time.time() - start_time
    print(f"[INFO] Trajanje upita /dashboard: {duration:.4f} sekundi")

    return render_template(
        "dashboard.html",
        hotels=hotels,
        zupanije=zupanije,
        ocjene=ocjene,
        zvjezdice=zvjezdice,
        source=source,
        user_email=user_name
    )


@app.route("/add_favorite/<hotel_code>", methods=["POST"])
def add_favorite(hotel_code):
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Morate biti prijavljeni."}), 401

    user_email = session["user_email"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM favorites WHERE email=%s AND HotelCode=%s", (user_email, hotel_code))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Hotel je već u favoritima."})

    cursor.execute("INSERT INTO favorites (email, HotelCode) VALUES (%s, %s)", (user_email, hotel_code))
    conn.commit()

    if not r.exists(f"hotel:{hotel_code}"):
        cursor.execute("SELECT HotelName, Address FROM hotels WHERE HotelCode=%s", (hotel_code,))
        hotel = cursor.fetchone()
        if hotel:
            r.hset(f"hotel:{hotel_code}", "HotelName", hotel["HotelName"] or "")
            r.hset(f"hotel:{hotel_code}", "Address", hotel["Address"] or "")

    cursor.close()
    conn.close()

    r.zincrby("hotel_favorites", 1, hotel_code)

    return jsonify({"success": True, "message": "Hotel dodan u favorite!"})


@app.route("/favorites")
def favorites():
    
    if "user_email" not in session:
        return redirect("/login")

    user_email = session["user_email"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT h.HotelCode, h.HotelName, h.Address, h.HotelRating, h.Map
        FROM favorites f
        JOIN hotels h ON f.HotelCode = h.HotelCode
        WHERE f.email = %s
    """, (user_email,))
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()

    for h in hotels:
        print("Hotel:", h["HotelName"], "Map:", h["Map"]) 

        if h["Map"]:
            try:
                lat_raw, lon_raw = h["Map"].split("|")
                h["Latitude"] = float(lat_raw.strip().replace(",", "."))
                h["Longitude"] = float(lon_raw.strip().replace(",", "."))
            except Exception as e:
                print("Greška u parsiranju:", h["Map"], e)
                h["Latitude"] = None
                h["Longitude"] = None
        else:
            h["Latitude"] = None
            h["Longitude"] = None
            
    return render_template(
    "favorites.html",
    hotels=hotels,
    user_name=session.get("user_name"),
    user_email=session.get("user_email")
)


@app.route("/is_favorite/<hotel_code>")
def is_favorite(hotel_code):
    if "user_email" not in session:
        return jsonify({"favorite": False})

    user_email = session["user_email"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM favorites WHERE email=%s AND HotelCode=%s", (user_email, hotel_code))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify({"favorite": bool(result)})


@app.route("/remove_favorite/<hotel_code>", methods=["POST"])
def remove_favorite(hotel_code):
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Morate biti prijavljeni."}), 401

    user_email = session["user_email"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE email=%s AND HotelCode=%s", (user_email, hotel_code))
    rows_deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if rows_deleted > 0:
        r.zincrby("hotel_favorites", -1, hotel_code)

    return jsonify({"success": True, "message": "Hotel uklonjen iz favorita!"})


@app.route("/logout")
def logout():
    session.clear()  
    return redirect("/")


@app.route("/top_hotels")
def top_hotels():
    user_email = session.get("user_email")
    user_name = user_email.split("@")[0] if user_email else ""

    top_hotels_codes = r.zrevrange("hotel_favorites", 0, 9, withscores=True)

    hotels = []
    for code, score in top_hotels_codes:
        if int(score) <= 0:
            continue
        code = code.decode("utf-8")
        hotel_data = r.hgetall(f"hotel:{code}")
        if hotel_data:
            hotels.append({
                "HotelCode": code,
                "HotelName": hotel_data[b"HotelName"].decode("utf-8"),
                "Address": hotel_data[b"Address"].decode("utf-8"),
                "favorite_count": int(score)
            })

    return render_template(
        "top_hotels.html",
        hotels=hotels,
        user_email=user_name
    )


@app.route("/user_account", methods=["GET", "POST"])
def user_account():
    user_email = session.get("user_email")
    user_name = user_email.split("@")[0] if user_email else ""
    if not user_email:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        address = request.form.get("address")

        cursor.execute("SELECT * FROM user_profiles WHERE email = %s", (user_email,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE user_profiles
                SET first_name=%s, last_name=%s, phone=%s, address=%s
                WHERE email=%s
            """, (first_name, last_name, phone, address, user_email))
        else:
            cursor.execute("""
                INSERT INTO user_profiles (email, first_name, last_name, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_email, first_name, last_name, phone, address))

        conn.commit()
        flash("Podaci su spremljeni!", "success")
        return redirect(url_for("user_account"))

    cursor.execute("SELECT * FROM user_profiles WHERE email = %s", (user_email,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("user_account.html", user_data=user_data, user_email=user_name)

if __name__ == '__main__':
    app.run(debug=True)
