module.exports = {
  apps: [
    {
      name: 'smartems',
      script: 'node_modules/@vue/cli-service/bin/vue-cli-service.js',
      args: 'serve --port 3000',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
    },
  ],
};
