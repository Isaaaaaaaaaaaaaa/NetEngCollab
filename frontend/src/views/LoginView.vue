<template>
  <div class="login-bg">
    <div class="login-shell app-card float-in">
      <div style="padding: 26px 26px 22px; display: flex; flex-direction: column; gap: 24px;">
        <div>
          <div style="font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase; color: #7f56d9; margin-bottom: 8px;">
            Network Engineering
          </div>
          <h1 style="font-size: 26px; font-weight: 600; margin: 0 0 8px 0; color: #111827;">
            网络工程专业师生协作平台
          </h1>
          <p style="font-size: 13px; line-height: 1.7; color: #667085; margin: 0;">
            将科研项目、大创、竞赛与学生能力画像统一到一个平台中，实现项目与人才的精准匹配，让每一次合作都可追踪、可沉淀、可复用。
          </p>
        </div>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-card shadow="hover" body-style="padding: 10px 12px; min-height: 72px;">
              <div style="font-size: 12px; font-weight: 500; margin-bottom: 4px;">科研项目</div>
              <div style="font-size: 12px; color: #667085;">项目招募、进度管理与成果沉淀。</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" body-style="padding: 10px 12px; min-height: 72px;">
              <div style="font-size: 12px; font-weight: 500; margin-bottom: 4px;">竞赛与大创</div>
              <div style="font-size: 12px; color: #667085;">从组队、备赛到复盘的一体化工作流。</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" body-style="padding: 10px 12px; min-height: 72px;">
              <div style="font-size: 12px; font-weight: 500; margin-bottom: 4px;">师生画像</div>
              <div style="font-size: 12px; color: #667085;">技能与合作记录形成可视化档案。</div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      <div style="padding: 26px 26px 22px; border-left: 1px solid rgba(15, 23, 42, 0.06);">
        <div style="margin-bottom: 18px;">
          <div class="page-title" style="font-size: 18px;">登录平台</div>
          <div class="page-subtitle">选择角色，使用学号 / 工号作为账号登录系统</div>
        </div>
        <el-form :model="form" label-position="top" size="large" @submit.prevent>
          <el-form-item label="登录角色">
            <el-radio-group v-model="form.role">
              <el-radio-button v-for="r in roles" :key="r.value" :label="r.value">
                {{ r.label }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="账号（学号 / 工号）">
            <el-input v-model="form.username" placeholder="如 221002501 / 10010001" clearable />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" placeholder="示例：admin123" show-password />
          </el-form-item>
        <div style="min-height: 18px; font-size: 12px; color: #f04438; margin-bottom: 4px;">
          {{ error }}
        </div>
          <el-form-item>
            <el-button
              type="primary"
              style="width: 100%;"
              :loading="loading"
              @click="onSubmit"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../store/auth";


const roles = [
  { value: "student", label: "学生" },
  { value: "teacher", label: "教师" },
  { value: "admin", label: "管理员" }
];


const form = reactive({
  role: "student",
  username: "",
  password: ""
});

const loading = ref(false);
const error = ref("");
const router = useRouter();
const route = useRoute();
const auth = useAuthStore();


async function onSubmit() {
  error.value = "";
  if (!form.username || !form.password || !form.role) {
    error.value = "请完整填写登录信息";
    return;
  }
  loading.value = true;
  try {
    const user = await auth.login(form.username, form.password, form.role);
    const redirect = (route.query.redirect as string) || null;
    if (user.must_change_password) {
      router.replace({ name: "change-password" });
      return;
    }
    if (redirect) {
      router.replace(redirect);
      return;
    }
    if (user.role === "student") {
      router.replace({ name: "student-dashboard" });
    } else if (user.role === "teacher") {
      router.replace({ name: "teacher-dashboard" });
    } else if (user.role === "admin") {
      router.replace({ name: "admin-dashboard" });
    }
  } catch (e: any) {
    error.value = e?.response?.data?.message || "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>
