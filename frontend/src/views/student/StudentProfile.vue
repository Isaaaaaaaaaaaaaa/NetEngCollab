<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的技能与合作意愿</h2>
        <p class="page-subtitle">信息越完整，匹配到合适项目和老师的概率越高</p>
      </div>
      <el-button type="primary" size="small" @click="save">保存</el-button>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="14">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">基础画像</div>
          </template>
          <el-form :model="form" label-position="top" size="small">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="专业方向">
                  <el-input v-model="form.direction" placeholder="如：网络安全、人工智能、物联网" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="兴趣领域标签（逗号分隔）">
                  <el-input v-model="interestsInput" placeholder="如：深度学习, 网络攻防" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="每周可投入时间（小时）">
                  <el-input-number v-model="form.weekly_hours" :min="0" :max="60" controls-position="right" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="合作偏好">
                  <el-space direction="vertical" :size="4">
                    <el-checkbox v-model="form.prefer_local">优先本地项目</el-checkbox>
                    <el-checkbox v-model="form.accept_cross">接受跨方向合作</el-checkbox>
                  </el-space>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="信息可见范围">
              <el-select v-model="form.visibility" style="width: 200px;">
                <el-option label="公开" value="public" />
                <el-option label="仅教师可见" value="teacher_only" />
                <el-option label="仅学生可见" value="student_only" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card class="app-card" shadow="never" style="margin-bottom: 14px;">
          <template #header>
            <div class="page-subtitle">技能列表</div>
          </template>
          <el-form label-position="top" size="small">
            <el-row :gutter="8" style="margin-bottom: 8px;">
              <el-col :span="13">
                <el-form-item label="技能名称">
                  <el-input v-model="skillName" placeholder="如：Python" />
                </el-form-item>
              </el-col>
              <el-col :span="7">
                <el-form-item label="熟练度">
                  <el-select v-model="skillLevel">
                    <el-option label="熟练" value="熟练" />
                    <el-option label="了解" value="了解" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="4" style="display:flex; align-items:flex-end;">
                <el-button type="primary" plain size="small" style="width:100%;" @click="addSkill">添加</el-button>
              </el-col>
            </el-row>
          </el-form>
          <div v-if="form.skills.length" style="display:flex; flex-wrap:wrap; gap:6px;">
            <el-tag
              v-for="s in form.skills"
              :key="s.name + s.level"
              type="info"
              effect="plain"
            >
              {{ s.name }} · {{ s.level }}
            </el-tag>
          </div>
          <el-empty v-else description="还没有维护技能，可从左侧添加" />
        </el-card>

        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">项目链接（GitHub、个人站点等）</div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="新链接">
              <el-input v-model="linkInput" placeholder="粘贴链接后点击添加" />
            </el-form-item>
            <el-form-item>
              <el-button size="small" type="primary" plain @click="addLink">添加链接</el-button>
            </el-form-item>
          </el-form>
          <el-empty v-if="!form.project_links.length" description="暂无链接" />
          <el-scrollbar v-else style="max-height: 150px; margin-top: 4px;">
            <ul style="list-style:none; padding:0; margin:0; font-size:11px; color:var(--app-muted);">
              <li v-for="l in form.project_links" :key="l" style="padding:2px 0;" class="truncate">{{ l }}</li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="savedHint" style="font-size: 12px; color: #16a34a;">已保存，匹配推荐将在几秒内更新。</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import axios from "axios";


const form = reactive<any>({
  direction: "",
  skills: [] as any[],
  project_links: [] as string[],
  interests: [] as string[],
  weekly_hours: null as number | null,
  prefer_local: false,
  accept_cross: true,
  visibility: "public"
});

const interestsInput = ref("");
const skillName = ref("");
const skillLevel = ref("熟练");
const linkInput = ref("");
const savedHint = ref(false);


async function load() {
  try {
    const resp = await axios.get("/api/student-profile");
    Object.assign(form, resp.data);
    interestsInput.value = (form.interests || []).join(", ");
  } catch (e) {
  }
}


async function save() {
  const interests = interestsInput.value
    .split(/[,，]/)
    .map(x => x.trim())
    .filter(x => x);
  await axios.put("/api/student-profile", {
    ...form,
    interests
  });
  savedHint.value = true;
  setTimeout(() => {
    savedHint.value = false;
  }, 3000);
}


function addSkill() {
  if (!skillName.value) return;
  form.skills.push({ name: skillName.value, level: skillLevel.value });
  skillName.value = "";
}


function addLink() {
  if (!linkInput.value) return;
  form.project_links.push(linkInput.value);
  linkInput.value = "";
}


onMounted(() => {
  load();
});
</script>
