<template>
  <div class="page profile-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的画像</h2>
        <p class="page-subtitle">完善画像用于项目匹配与导师推荐</p>
      </div>
    </div>

    <el-card class="app-card profile-card" shadow="never" style="margin-top:6px;">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <el-tab-pane label="画像信息" name="profile">
          <el-scrollbar class="profile-scroll">
            <div class="section">
              <div class="section-title">基础信息</div>
              <el-form :model="form" label-position="top" size="small">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12">
                    <el-form-item label="专业方向">
                      <el-input v-model="form.direction" placeholder="如：网络安全、人工智能、物联网" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="12">
                    <el-form-item label="兴趣标签（逗号分隔）">
                      <el-input v-model="interestsInput" placeholder="如：深度学习, 网络攻防" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="每周可投入时间（小时）">
                      <el-input-number v-model="form.weekly_hours" :min="0" :max="60" controls-position="right" style="width:100%;" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="信息可见范围">
                      <el-select v-model="form.visibility" style="width: 100%;">
                        <el-option label="公开" value="public" />
                        <el-option label="仅教师可见" value="teacher_only" />
                        <el-option label="仅学生可见" value="student_only" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="合作偏好">
                      <el-space wrap :size="10">
                        <el-checkbox v-model="form.prefer_local">优先本地</el-checkbox>
                        <el-checkbox v-model="form.accept_cross">跨方向</el-checkbox>
                      </el-space>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
              <div style="text-align:right; margin-top:8px;">
                <el-button type="primary" size="small" @click="save">保存基础信息</el-button>
              </div>
            </div>

            <el-divider />

            <el-row :gutter="16" class="profile-bottom">
              <el-col :xs="24" :lg="10">
                <div class="section section-fill">
                  <div class="section-title">技能标签</div>
                  <el-form label-position="top" size="small">
                    <el-form-item label="添加技能">
                      <div class="inline-form">
                        <el-input v-model="skillName" placeholder="如：Python" />
                        <el-select v-model="skillLevel" style="width: 120px;">
                          <el-option label="熟练" value="熟练" />
                          <el-option label="了解" value="了解" />
                        </el-select>
                        <el-button type="primary" plain size="small" @click="addSkill">添加</el-button>
                      </div>
                    </el-form-item>
                  </el-form>

                  <el-scrollbar v-if="form.skills.length" class="fill-scroll">
                    <div style="display:flex; flex-wrap:wrap; gap:8px; padding-right:6px;">
                      <el-tag
                        v-for="s in form.skills"
                        :key="s.name + s.level"
                        type="info"
                        effect="plain"
                        closable
                        @close="removeSkill(s)"
                      >
                        {{ s.name }} · {{ s.level }}
                      </el-tag>
                    </div>
                  </el-scrollbar>
                  <el-empty v-else description="暂无技能" />
                </div>
              </el-col>

              <el-col :xs="24" :lg="14">
                <div class="section section-fill">
                  <div class="section-title">项目链接</div>
                  <el-form label-position="top" size="small">
                    <el-form-item label="新链接">
                      <div class="inline-form link-form">
                        <div class="grow">
                          <el-input v-model="linkInput" placeholder="GitHub、博客、作品集链接" />
                        </div>
                        <el-button size="small" type="primary" plain @click="addLink">添加</el-button>
                      </div>
                    </el-form-item>
                  </el-form>

                  <el-scrollbar v-if="form.project_links.length" class="fill-scroll">
                    <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text); padding-right:6px;">
                      <li
                        v-for="l in form.project_links"
                        :key="l"
                        style="padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.2); display:flex; align-items:center; justify-content:space-between; gap:8px;"
                      >
                        <span class="truncate" style="flex:1 1 auto;">
                          {{ l }}
                        </span>
                        <el-button size="small" text type="danger" @click="removeLink(l)">删除</el-button>
                      </li>
                    </ul>
                  </el-scrollbar>
                  <el-empty v-else description="暂无链接" />
                </div>
              </el-col>
            </el-row>
          </el-scrollbar>
        </el-tab-pane>

        <el-tab-pane label="项目经历" name="experiences">
          <el-scrollbar class="profile-scroll">
            <div class="section">
              <div class="section-title">项目经历</div>
              <el-form label-position="top" size="small">
                <el-row :gutter="8">
                  <el-col :xs="24" :sm="6">
                    <el-form-item label="类型">
                      <el-select v-model="expForm.type" style="width:100%;">
                        <el-option label="科研" value="科研" />
                        <el-option label="大创" value="大创" />
                        <el-option label="竞赛" value="竞赛" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="18">
                    <el-form-item label="标题">
                      <el-input v-model="expForm.title" placeholder="如：基于深度学习的入侵检测" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="8">
                  <el-col :xs="24" :sm="12">
                    <el-form-item label="时间">
                      <el-input v-model="expForm.time" placeholder="如：2024.03 - 2024.10" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="12">
                    <el-form-item label="成果">
                      <el-input v-model="expForm.outcome" placeholder="如：二等奖 / 论文 / Demo" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="内容">
                  <el-input v-model="expForm.content" type="textarea" :rows="3" placeholder="简述你负责的工作与亮点" />
                </el-form-item>
                <div style="text-align:right;">
                  <el-button size="small" type="primary" plain @click="addExperience">
                    {{ editingExpIndex !== null ? "保存修改" : "添加经历" }}
                  </el-button>
                </div>
              </el-form>

              <el-empty v-if="!form.experiences.length" description="暂无项目经历" />
              <el-table v-else :data="form.experiences" size="small" border style="width:100%; margin-top:8px;">
                <el-table-column prop="type" label="类型" width="70" />
                <el-table-column prop="title" label="标题" min-width="260" show-overflow-tooltip />
                <el-table-column prop="time" label="时间" width="120" />
                <el-table-column prop="outcome" label="成果" width="120" show-overflow-tooltip />
                <el-table-column label="操作" width="140" align="right">
                  <template #default="scope">
                    <div class="table-actions">
                      <el-button size="small" text @click="editExperience(scope.$index)">编辑</el-button>
                      <el-button size="small" text type="danger" @click="removeExperience(scope.$index)">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-scrollbar>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <div v-if="savedHint" style="font-size: 12px; color: #16a34a; margin-top: 10px;">已保存，匹配推荐将在几秒内更新。</div>
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
  experiences: [] as any[],
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
const activeTab = ref<"profile" | "experiences">("profile");
const editingExpIndex = ref<number | null>(null);

const expForm = reactive<any>({
  type: "科研",
  title: "",
  content: "",
  outcome: "",
  time: ""
});


async function load() {
  try {
    const resp = await axios.get("/api/student-profile");
    Object.assign(form, resp.data);
    interestsInput.value = (form.interests || []).join(", ");
  } catch (e) {
  }
}


async function save() {
  await syncProfile(true);
}


async function syncProfile(showHint = false) {
  const interests = interestsInput.value
    .split(/[,，]/)
    .map(x => x.trim())
    .filter(x => x);
  await axios.put("/api/student-profile", {
    ...form,
    interests
  });
  if (showHint) {
    savedHint.value = true;
    setTimeout(() => {
      savedHint.value = false;
    }, 3000);
  }
}


function addSkill() {
  if (!skillName.value) return;
  form.skills.push({ name: skillName.value, level: skillLevel.value });
  skillName.value = "";
  syncProfile(false);
}


function removeSkill(s: any) {
  const idx = form.skills.findIndex((x: any) => x.name === s.name && x.level === s.level);
  if (idx !== -1) {
    form.skills.splice(idx, 1);
    syncProfile(false);
  }
}


function addLink() {
  if (!linkInput.value) return;
  form.project_links.push(linkInput.value);
  linkInput.value = "";
  syncProfile(false);
}


function removeLink(l: string) {
  const idx = form.project_links.indexOf(l);
  if (idx !== -1) {
    form.project_links.splice(idx, 1);
    syncProfile(false);
  }
}


function addExperience() {
  if (!expForm.title || !expForm.content) return;
  if (editingExpIndex.value !== null && editingExpIndex.value >= 0 && editingExpIndex.value < form.experiences.length) {
    const target = form.experiences[editingExpIndex.value];
    target.type = expForm.type;
    target.title = expForm.title;
    target.content = expForm.content;
    target.outcome = expForm.outcome;
    target.time = expForm.time;
  } else {
    form.experiences.push({
      type: expForm.type,
      title: expForm.title,
      content: expForm.content,
      outcome: expForm.outcome,
      time: expForm.time
    });
  }
  expForm.title = "";
  expForm.content = "";
  expForm.outcome = "";
  expForm.time = "";
  editingExpIndex.value = null;
  syncProfile(false);
}


function removeExperience(idx: number) {
  form.experiences.splice(idx, 1);
  syncProfile(false);
}


function editExperience(idx: number) {
  const e = form.experiences[idx];
  if (!e) return;
  editingExpIndex.value = idx;
  expForm.type = e.type || "科研";
  expForm.title = e.title || "";
  expForm.content = e.content || "";
  expForm.outcome = e.outcome || "";
  expForm.time = e.time || "";
}


onMounted(() => {
  load();
});
</script>

<style scoped>
.profile-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.profile-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.profile-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.profile-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.profile-tabs :deep(.el-tabs__content) {
  flex: 1 1 auto;
  min-height: 0;
}

.profile-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.profile-scroll {
  height: 100%;
}

.section {
  padding: 10px 6px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
}

.profile-bottom :deep(.el-col) {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-fill {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.inline-form {
  display: flex;
  gap: 8px;
  align-items: center;
}

.grow {
  flex: 1 1 auto;
  min-width: 200px;
}

.link-form :deep(.el-input) {
  width: 100%;
}

.table-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  white-space: nowrap;
}

.inline-form :deep(.el-input),
.inline-form :deep(.el-select) {
  flex: 1 1 auto;
  min-width: 0;
}

.fill-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
