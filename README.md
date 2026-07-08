# Employee Management System

A Flask-based employee management system with:
- user registration and login
- employee record storage
- help desk support requests
- dashboard view for tracking records

## Run locally

1. Create a virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app
   ```bash
   python app.py
   ```
4. Open your browser at
   ```text
   http://127.0.0.1:5000
   ```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Deploy to GitHub and Heroku

1. Initialize Git
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
2. Create a repository on GitHub.
3. Connect the remote
   ```bash
   git remote add origin https://github.com/your-username/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```
4. Deploy on Heroku
   ```bash
   heroku create
   heroku git:remote -a your-heroku-app-name
   git push heroku main
   ```

## Notes

- Set a secret key in production:
  ```bash
  heroku config:set SECRET_KEY=your-secret-key
  ```
