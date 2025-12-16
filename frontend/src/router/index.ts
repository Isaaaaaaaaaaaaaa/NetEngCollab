import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import { useAuthStore } from "../store/auth";

const LoginView = () => import("../views/LoginView.vue");
const StudentLayout = () => import("../views/student/StudentLayout.vue");
const TeacherLayout = () => import("../views/teacher/TeacherLayout.vue");
const AdminLayout = () => import("../views/admin/AdminLayout.vue");
const StudentDashboard = () => import("../views/student/StudentDashboard.vue");
const TeacherDashboard = () => import("../views/teacher/TeacherDashboard.vue");
const AdminDashboard = () => import("../views/admin/AdminDashboard.vue");
const AdminAnalytics = () => import("../views/admin/AdminAnalytics.vue");
const StudentProjects = () => import("../views/student/StudentProjects.vue");
const StudentProfile = () => import("../views/student/StudentProfile.vue");
const StudentCooperation = () => import("../views/student/StudentCooperation.vue");
const TeacherPosts = () => import("../views/teacher/TeacherPosts.vue");
const TeacherStudents = () => import("../views/teacher/TeacherStudents.vue");
const TeacherProjects = () => import("../views/teacher/TeacherProjects.vue");
const AdminUsers = () => import("../views/admin/AdminUsers.vue");
const AdminCooperations = () => import("../views/admin/AdminCooperations.vue");
const ResourcesCenter = () => import("../views/common/ResourcesCenter.vue");
const ForumView = () => import("../views/common/ForumView.vue");
const TeamupView = () => import("../views/common/TeamupView.vue");
const MessagesView = () => import("../views/common/MessagesView.vue");


const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: LoginView
  },
  {
    path: "/",
    redirect: "/login"
  },
  {
    path: "/student",
    component: StudentLayout,
    meta: { requiresAuth: true, role: "student" },
    children: [
      { path: "dashboard", name: "student-dashboard", component: StudentDashboard },
      { path: "projects", name: "student-projects", component: StudentProjects },
      { path: "cooperation", name: "student-cooperation", component: StudentCooperation },
      { path: "profile", name: "student-profile", component: StudentProfile },
      { path: "resources", name: "student-resources", component: ResourcesCenter },
      { path: "forum", name: "student-forum", component: ForumView },
      { path: "teamup", name: "student-teamup", component: TeamupView },
      { path: "messages", name: "student-messages", component: MessagesView }
    ]
  },
  {
    path: "/teacher",
    component: TeacherLayout,
    meta: { requiresAuth: true, role: "teacher" },
    children: [
      { path: "dashboard", name: "teacher-dashboard", component: TeacherDashboard },
      { path: "posts", name: "teacher-posts", component: TeacherPosts },
      { path: "students", name: "teacher-students", component: TeacherStudents },
      { path: "projects", name: "teacher-projects", component: TeacherProjects },
      { path: "resources", name: "teacher-resources", component: ResourcesCenter },
      { path: "forum", name: "teacher-forum", component: ForumView },
      { path: "teamup", name: "teacher-teamup", component: TeamupView },
      { path: "messages", name: "teacher-messages", component: MessagesView }
    ]
  },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true, role: "admin" },
    children: [
      { path: "dashboard", name: "admin-dashboard", component: AdminDashboard },
      { path: "analytics", name: "admin-analytics", component: AdminAnalytics },
      { path: "users", name: "admin-users", component: AdminUsers },
      { path: "projects", name: "admin-projects", component: AdminCooperations }
    ]
  }
];


const router = createRouter({
  history: createWebHistory(),
  routes
});


router.beforeEach((to, from, next) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth) {
    if (!auth.isAuthenticated) {
      next({ name: "login", query: { redirect: to.fullPath } });
      return;
    }
    const role = to.meta.role as string;
    if (role && auth.user?.role !== role) {
      if (auth.user?.role === "student") {
        next({ name: "student-dashboard" });
      } else if (auth.user?.role === "teacher") {
        next({ name: "teacher-dashboard" });
      } else if (auth.user?.role === "admin") {
        next({ name: "admin-dashboard" });
      } else {
        next({ name: "login" });
      }
      return;
    }
  }
  next();
});


export default router;
