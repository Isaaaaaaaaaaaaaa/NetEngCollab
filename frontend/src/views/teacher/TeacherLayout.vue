<template>
  <el-container class="app-shell">
    <el-header height="70px" style="border-bottom: 1px solid rgba(15, 23, 42, 0.06); background: rgba(255, 255, 255, 0.92);">
      <div class="app-container" style="display: flex; align-items: center; justify-content: space-between; gap: 18px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 32px; height: 32px; border-radius: 999px; background: linear-gradient(135deg, #f59e0b, #f43f5e); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; font-weight: 600;">
            T
          </div>
          <div>
            <div style="font-size: 14px; font-weight: 600;">教师工作台</div>
            <div style="font-size: 12px; color: #98a2b3;">项目招募、学生画像与合作管理中心</div>
          </div>
        </div>
        <el-space :size="8">
          <router-link :to="{ name: 'teacher-dashboard' }">
            <el-button text size="small">总览</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-posts' }">
            <el-button text size="small">项目与竞赛</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-students' }">
            <el-button text size="small">学生匹配</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-projects' }">
            <el-button text size="small">合作项目</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-resources' }">
            <el-button text size="small">资源库</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-forum' }">
            <el-button text size="small">讨论区</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-teamup' }">
            <el-button text size="small">组队互助</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-messages' }">
            <el-button text size="small">私信</el-button>
          </router-link>
          <notifications-bell />
          <el-button size="small" type="primary" plain @click="logout">退出</el-button>
        </el-space>
      </div>
    </el-header>
    <el-main style="padding: 16px 0 28px; background: transparent;">
      <div class="app-container">
        <router-view />
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "../../store/auth";
import NotificationsBell from "../../components/NotificationsBell.vue";


const auth = useAuthStore();
const router = useRouter();


function logout() {
  auth.logout();
  router.replace({ name: "login" });
}
</script>
