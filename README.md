# Redis-base
# 🏨 Flask Aplikacija

Ovo je web aplikacija napravljena pomoću **Flaska** koja omogućava:
- registraciju i prijavu korisnika  
- spremanje korisnika i podataka o hotelima u **MySQL**  
- korištenje **Redis-a** za keširanje i praćenje pokušaja prijave  
- pregled i filtriranje hotela  
- dodavanje hotela u favorite i prikaz najpopularnijih  
- statistiku i dashboard s agregiranim podacima  

---

## 📋 Preduvjeti

Prije pokretanja aplikacije, potrebno je 

- Preuzeti hotel.csv (https://www.kaggle.com/datasets/raj713335/tbo-hotels-dataset)
- pip install flask
- pip install redis
- pip install mysql-connector-python

- instalirati MySQL (https://dev.mysql.com/downloads/)


- [Python 3.9+](https://www.python.org/downloads/)  
- [MySQL](https://dev.mysql.com/downloads/)  
- [Redis](https://redis.io/download)  

Također, kreirati MySQL bazu podataka **hotelmatch** i potrebne tablice (`users`, `hotels`, `favorites`, `user_profiles`) dostupne u create.sql.

---

## 🚀 Pokretanje projekta

1. Kloniraj repozitorij:

```bash
git clone https://github.com/tvoje-ime/hotelmatch.git
cd hotelmatch
