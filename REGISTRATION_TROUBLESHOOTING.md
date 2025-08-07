# 🐛 REGISTRATION TROUBLESHOOTING GUIDE

## ✅ **Issues Fixed:**
1. **API Endpoint Mismatch** - Frontend was calling `/api/user/register` but backend expects `/api/user` with `action: 'create'`
2. **Login Endpoint Mismatch** - Frontend was calling `/api/user/login` but backend expects `/api/user` with `action: 'login'`

## 🚀 **Upload Updated File:**
Upload the updated `frontend/js/app.js` file to fix the registration API calls.

## 🧪 **Test Registration Manually:**

### **Method 1: Browser Console Test**
1. Open your website
2. Press F12 to open Developer Tools
3. Go to Console tab
4. Run this test:

```javascript
// Test user registration
fetch('/api/user', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        action: 'create',
        username: 'testuser',
        email: 'test@example.com',
        password: 'testpass123'
    })
})
.then(response => response.json())
.then(data => console.log('Registration result:', data))
.catch(error => console.error('Registration error:', error));
```

### **Method 2: cURL Test**
From PythonAnywhere console:
```bash
curl -X POST https://laukayson.pythonanywhere.com/api/user \
  -H "Content-Type: application/json" \
  -d '{"action":"create","username":"testuser2","email":"test2@example.com","password":"testpass123"}'
```

## 🔍 **Expected Results:**

### **Success Response:**
```json
{
  "user_id": 1,
  "status": "success"
}
```

### **Error Responses:**
```json
{
  "error": "All fields required"
}
```
```json
{
  "error": "Username or email already exists"
}
```

## 🐛 **Common Issues:**

### **Issue 1: Database Not Writable**
**Symptoms:** SQLite errors
**Fix:**
```bash
chmod 755 /home/laukayson/englishlearningapp/data
chmod 755 /home/laukayson/englishlearningapp/data/db
chmod 644 /home/laukayson/englishlearningapp/data/db/language_app.db
```

### **Issue 2: Missing Password Field**
**Symptoms:** "All fields required" error
**Fix:** Registration form needs username, email, and password fields

### **Issue 3: Frontend/Backend Mismatch**
**Symptoms:** 404 or 500 errors
**Fix:** Upload updated `app.js` file (already fixed above)

## 📋 **Registration Flow:**

1. **Frontend Form** → Collects username, email, password
2. **API Call** → `POST /api/user` with `action: 'create'`
3. **Backend Processing** → Validates data, hashes password
4. **Database Insert** → Creates user record and user_stats record
5. **Response** → Returns user_id and success status

## ✅ **Test Checklist:**

- [ ] Updated `app.js` uploaded to PythonAnywhere
- [ ] Web app reloaded
- [ ] Database file exists and is writable
- [ ] Manual API test works (browser console)
- [ ] Registration form works on website
- [ ] No errors in browser console
- [ ] No errors in PythonAnywhere error logs

After uploading the fixed `app.js` file, your registration should work! 🎉
