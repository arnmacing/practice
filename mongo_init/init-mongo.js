db.createUser({
  user: 'mongoadmin',
  pwd: 'secret',
  roles: [
    {
      role: 'readWrite',
      db: 'service',
    },
    {
      role: 'dbAdmin',
      db: 'service',
    },
  ],
});
