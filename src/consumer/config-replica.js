rsconf = {
  _id: "rs0",
  members: [{ _id: 0, host: "mongo1:27017", priority: 1.0 }],
};
rs.initiate(rsconf);
rs.status();

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

