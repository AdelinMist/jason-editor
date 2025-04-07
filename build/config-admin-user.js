conn = Mongo("mongodb://mongo1/?directConnection=true");
db = conn.getDB("admin");
db.createUser(
  {
    user: "admin",
    pwd: "admin", // or cleartext password
    roles: [
      { role: "userAdminAnyDatabase", db: "admin" },
      { role: "readWriteAnyDatabase", db: "admin" }
    ]
  }
)