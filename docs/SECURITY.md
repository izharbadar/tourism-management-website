# Security controls already applied

- CSRF protection for unsafe requests and browser fetch requests
- Rate limits for login, registration, inquiries, bookings, reviews and search
- HttpOnly and SameSite session/remember cookies
- Secure-cookie and HSTS support for HTTPS production
- Security response headers and CSP report-only policy
- Custom 400, 403, 404, 413, 429 and 500 pages
- Admin role checks on admin routes
- Image verification, random upload names and pixel/file limits
- `.env`, logs, caches, backups and archives excluded from source control
- Rotating security logs without password/token values
- Development test route removed from the production package
- Production configuration validation before application startup

Production credentials and the final secret key must be set only in the
server-side `.env` file.
