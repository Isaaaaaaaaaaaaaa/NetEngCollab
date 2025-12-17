<template>
  <div class="page">
    <div class="page-inner" style="max-width:520px; margin:40px auto;">
      <el-card class="app-card" shadow="never">
        <template #header>
          <div class="page-title">修改密码</div>
          <div class="page-subtitle">
            为了账号安全，请设置一个只属于你的新密码（至少 6 位）。
          </div>
        </template>
        <el-form :model="form" label-position="top" size="large">
          <el-form-item label="当前密码">
            <el-input v-model="form.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="form.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="form.confirm_password" type="password" show-password />
          </el-form-item>
          <div class="error-text">{{ error }}</div>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width:100%;" @click="onSubmit">
              保存新密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../../store/auth";


const form = reactive({
  old_password: "",
  new_password: "",
  confirm_password: ""
});

const error = ref("");
const loading = ref(false);

const router = useRouter();
const auth = useAuthStore();


async function onSubmit() {
  error.value = "";
  if (!form.old_password || !form.new_password || !form.confirm_password) {
    error.value = "请完整填写密码信息";
    return;
  }
  if (form.new_password.length < 6) {
    error.value = "新密码长度至少 6 位";
    return;
  }
  if (form.new_password !== form.confirm_password) {
    error.value = "两次输入的新密码不一致";
    return;
  }
  loading.value = true;
  try {
    await axios.post("/api/auth/change-password", {
      old_password: form.old_password,
      new_password: form.new_password
    });
    ElMessage.success("密码修改成功，请牢记新密码");
    if (auth.user) {
      auth.user.must_change_password = false;
      localStorage.setItem("user", JSON.stringify(auth.user));
    }
    if (auth.user?.role === "student") {
      router.replace({ name: "student-dashboard" });
    } else if (auth.user?.role === "teacher") {
      router.replace({ name: "teacher-dashboard" });
    } else if (auth.user?.role === "admin") {
      router.replace({ name: "admin-dashboard" });
    } else {
      router.replace({ name: "login" });
    }
  } catch (e: any) {
    error.value = e?.response?.data?.message || "修改密码失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: stretch;
}

.page-inner {
  width: 100%;
}

.error-text {
  min-height: 18px;
  font-size: 12px;
  color: #f04438;
  margin-bottom: 4px;
}
</style>

