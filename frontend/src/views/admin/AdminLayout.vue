<template>
  <el-container class="app-shell">
    <el-header height="70px" style="border-bottom: 1px solid rgba(15, 23, 42, 0.06); background: rgba(255, 255, 255, 0.92);">
      <div class="app-container" style="display: flex; align-items: center; justify-content: space-between; gap: 18px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 32px; height: 32px; border-radius: 999px; background: linear-gradient(135deg, #22c55e, #0ea5e9); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; font-weight: 600;">
            A
          </div>
          <div>
            <div style="font-size: 14px; font-weight: 600;">管理员控制台</div>
            <div style="font-size: 12px; color: #98a2b3;">账号审核、内容审核与平台运营数据</div>
          </div>
        </div>
        <el-space :size="8">
          <router-link :to="{ name: 'admin-dashboard' }">
            <el-button text size="small">总览</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-analytics' }">
            <el-button text size="small">数据分析</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-users' }">
            <el-button text size="small">人员概览</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-projects' }">
            <el-button text size="small">项目概览</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-resources' }">
            <el-button text size="small">资源库</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-forum' }">
            <el-button text size="small">讨论区</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-teamup' }">
            <el-button text size="small">组队互助</el-button>
          </router-link>
          <router-link :to="{ name: 'admin-messages' }">
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
