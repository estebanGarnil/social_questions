import { createPinia } from "pinia"
import { createApp } from "vue"

import App from "./App.vue"
import router from "./router"
import { useAuthStore } from "./stores/auth"
import "./styles/main.css"

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  const auth = useAuthStore(pinia)
  await auth.initialize()

  app.use(router)
  app.mount("#app")
}

void bootstrap()
