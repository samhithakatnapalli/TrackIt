# TrackIt Web App

A simple multi-user web app to track your books and shows — built using **Flask + SQLite**.

---

## Features

*  Track **To Read / Read** books
*  Track **To Watch / Watched** shows & movies
*  Multi-user support (no login, just enter your name)
*  Search items in your lists
*  Add new items
*  Delete items
*  View sorted lists

---

## Tech Stack

* **Backend:** Flask (Python)
* **Database:** SQLite
* **Frontend:** HTML, CSS
* **Deployment:** Render

---

## 🧠 How it works

* Users enter their name on entry
* Data is stored with a `user_name` field
* All users share one database but see only their own data
* Lists are separated using `list_name`:

  * `tbr`
  * `to_watch`
  * `read`
  * `watched`

---

## Deployment

Deployed using Render.

---

## Future Improvements

* Persistent cloud database (Supabase/PostgreSQL)
* User authentication (optional)
* Edit/update items
* Better UI/UX

---

## Author

Built by Samhitha 💛
