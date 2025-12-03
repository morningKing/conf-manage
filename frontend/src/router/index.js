import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/scripts'
  },
  {
    path: '/scripts',
    name: 'Scripts',
    component: () => import('../views/Scripts.vue')
  },
  {
    path: '/executions',
    name: 'Executions',
    component: () => import('../views/Executions.vue')
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('../views/Schedules.vue')
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('../views/Files.vue')
  },
  {
    path: '/environments',
    name: 'Environments',
    component: () => import('../views/Environments.vue')
  },
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('../views/Categories.vue')
  },
  {
    path: '/tags',
    name: 'Tags',
    component: () => import('../views/Tags.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
