<template>
  <el-config-provider namespace="el">
    <div class="app-shell">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
      <div
        style="position: fixed; right: 18px; bottom: 14px; font-size: 11px; color: #98a2b3; opacity: 0.85; user-select: none;"
      >
        网络工程专业师生协作平台
      </div>
      <notifications-panel />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { ElConfigProvider } from "element-plus";
import { useAuthStore } from "./store/auth";
import NotificationsPanel from "./components/NotificationsPanel.vue";


const auth = useAuthStore();

onMounted(() => {
  auth.initFromStorage();
});
</script>
