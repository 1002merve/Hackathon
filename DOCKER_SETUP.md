# How to use Docker with this Django project

## 1. Build the images

```
docker-compose build
```

## 2. Run migrations

```
docker-compose run migrate
```

## 3. Start the development server

```
docker-compose up web
```

The app will be available at http://localhost:8000

## 4. Stopping

```
docker-compose down
```

---

- The database (SQLite) is stored in the project directory and will persist between runs.
- For production, consider using a production-ready database and web server.
