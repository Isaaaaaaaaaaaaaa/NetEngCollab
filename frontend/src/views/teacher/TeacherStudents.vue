<template>
  <div class="page ts-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">学生画像与匹配</h2>
        <p class="page-subtitle">
          按专业、技能和关键词筛选学生，快速找到合适的合作伙伴
          <span v-if="selectedProjectId" style="color: #409eff; margin-left: 8px;">
            · 已选择项目，学生按匹配度排序
          </span>
        </p>
      </div>
      <el-space :size="8">
        <el-select v-model="selectedProjectId" size="small" clearable placeholder="选择项目计算匹配度" style="width: 220px;" @change="handleProjectChange">
          <template #prefix>
            <el-icon><Folder /></el-icon>
          </template>
          <el-option label="全部学生（通用推荐）" :value="null" />
          <el-option
            v-for="project in myProjects"
            :key="project.id"
            :label="project.title"
            :value="project.id"
          >
            <span>{{ project.title }}</span>
            <span style="float: right; color: #8492a6; font-size: 12px; margin-left: 8px;">
              {{ project.recruit_count ? `招${project.recruit_count}人` : '' }}
            </span>
          </el-option>
        </el-select>
        <el-select v-model="filters.grade" size="small" clearable placeholder="年级" style="width: 120px;">
          <el-option label="大一" value="大一" />
          <el-option label="大二" value="大二" />
          <el-option label="大三" value="大三" />
          <el-option label="大四" value="大四" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          size="small"
          placeholder="关键词，如 目标检测"
          style="width: 240px;"
          clearable
        />
        <el-button size="small" type="primary" plain @click="load">检索</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" class="ts-main" style="margin-top: 6px;">
      <el-col :xs="24" :lg="14">
        <el-card class="app-card ts-card" shadow="never">
          <template #header>
            <div class="page-subtitle">学生列表</div>
          </template>
          <el-empty v-if="!students.length" description="暂无学生记录" />
          <div v-else class="list-wrap">
            <div class="table-wrap">
              <el-table
                :data="pagedStudents"
                size="small"
                border
                @row-click="select"
                style="cursor:pointer; height:100%;"
              >
                <el-table-column label="姓名" min-width="120">
                  <template #default="scope">
                    <span style="font-size:13px; font-weight:500;">{{ scope.row.user.display_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="年级" width="90" align="center">
                  <template #default="scope">
                    <span style="font-size:12px;">{{ scope.row.grade || '未填写' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="技能" min-width="150">
                  <template #default="scope">
                    <div style="display:flex; flex-wrap:wrap; gap:4px;">
                      <span v-for="sk in scope.row.skills" :key="sk.name" class="tag">{{ sk.name }} · {{ sk.level }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="技能评分" width="100" align="center">
                  <template #default="scope">
                    <span v-if="scope.row.skill_score != null" class="pill" :class="scoreClass(scope.row.skill_score)" style="font-size:11px;">
                      {{ scope.row.skill_score }}
                    </span>
                    <span v-else style="font-size:11px; color:var(--app-muted);">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="每周时间" width="100" align="center">
                  <template #default="scope">
                    <span v-if="scope.row.weekly_hours" style="font-size:12px;">每周 {{ scope.row.weekly_hours }} 小时</span>
                    <span v-else style="font-size:12px; color:var(--app-muted);">未填写</span>
                  </template>
                </el-table-column>
                <el-table-column label="推荐度" width="110" align="center">
                  <template #default="scope">
                    <span v-if="recommendScores[scope.row.user.id]" class="pill badge-green" style="font-size:11px;">
                      匹配 {{ Math.round(recommendScores[scope.row.user.id] * 100) }}%
                    </span>
                    <span v-else style="font-size:11px; color:var(--app-muted);">无</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div v-if="totalStudents > pageSize" class="pager">
              <el-pagination
                background
                layout="prev, pager, next"
                :current-page="page"
                :page-size="pageSize"
                :total="totalStudents"
                @current-change="handlePageChange"
              />
            </div>
          </div>
        </el-card>
      </el-col>

          <el-col :xs="24" :lg="10">
        <el-card class="app-card ts-card" shadow="never">
          <template #header>
            <div class="page-subtitle">学生详情</div>
          </template>
          <div v-if="!selectedStudent" style="font-size:12px; color:var(--app-muted);">
            在左侧表格中选择一名学生查看详细画像。
          </div>
          <el-scrollbar v-else class="detail-scroll">
            <div style="display:flex; flex-direction:column; gap:10px; font-size:13px; padding-right:6px;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div>
                <div style="font-size:15px; font-weight:600;">{{ selectedStudent.user.display_name }}</div>
              </div>
              <div style="display:flex; gap:8px; align-items:center;">
                <div v-if="selectedStudent.skill_score != null" class="pill" :class="scoreClass(selectedStudent.skill_score)">
                  技能评分 {{ selectedStudent.skill_score }}
                </div>
                <div v-if="selectedStudent.weekly_hours" class="pill badge-green">每周 {{ selectedStudent.weekly_hours }} 小时</div>
              </div>
            </div>

            <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:12px; color:var(--app-text);">
              <span>专业：{{ selectedStudent.major || '未填写' }}</span>
              <span>年级：{{ selectedStudent.grade || '未填写' }}</span>
              <span>班级：{{ selectedStudent.class_name || '未填写' }}</span>
            </div>

            <div>
              技能标签：
              <span v-if="!selectedStudent.skills.length" style="color:var(--app-muted);">未填写</span>
            </div>
            <div v-if="selectedStudent.skills.length" style="display:flex; flex-wrap:wrap; gap:6px;">
              <span v-for="sk in selectedStudent.skills" :key="sk.name + sk.level" class="tag">{{ sk.name }} · {{ sk.level }}</span>
            </div>

            <div>
              兴趣标签：
              <span v-if="!selectedStudent.interests?.length" style="color:var(--app-muted);">未填写</span>
            </div>
            <div v-if="selectedStudent.interests?.length" style="display:flex; flex-wrap:wrap; gap:6px;">
              <span v-for="tag in selectedStudent.interests" :key="tag" class="tag">{{ tag }}</span>
            </div>

            <div>
              偏好：
              <span>{{ selectedStudent.prefer_local ? '优先本地' : '可远程' }}</span>
              ·
              <span>{{ selectedStudent.accept_cross ? '接受跨方向' : '方向匹配优先' }}</span>
            </div>

            <div>
              项目链接：
              <span v-if="!selectedStudent.project_links?.length" style="color:var(--app-muted);">暂无链接</span>
            </div>
            <ul v-if="selectedStudent.project_links?.length" style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="link in selectedStudent.project_links"
                :key="link"
                class="truncate"
                style="padding:4px 0; border-bottom:1px solid rgba(148,163,184,0.16);"
              >
                {{ link }}
              </li>
            </ul>

            <div>
              项目经历：
              <span v-if="!selectedStudent.experiences?.length" style="color:var(--app-muted);">暂无项目经历</span>
            </div>
            <ul v-if="selectedStudent.experiences?.length" style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="(exp, idx) in selectedStudent.experiences"
                :key="idx"
                style="padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.16);"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                  <span class="truncate" style="max-width:220px; font-weight:500;">{{ exp.title || '未命名项目' }}</span>
                  <span style="font-size:11px; color:var(--app-muted);">{{ exp.time || '' }}</span>
                </div>
                <div style="font-size:11px; color:var(--app-muted);">
                  {{ exp.type || '' }} · {{ exp.outcome || '' }}
                </div>
              </li>
            </ul>

            <div>
              简历文件：
              <span v-if="!selectedStudent.resume_file" style="color:var(--app-muted);">未上传</span>
            </div>
            <div v-if="selectedStudent.resume_file" style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <span class="truncate" style="max-width:260px; font-size:12px;">{{ selectedStudent.resume_file.original_name }}</span>
              <el-button size="small" text type="primary" @click.stop="downloadResume(selectedStudent.resume_file)">
                下载
              </el-button>
            </div>

            <div style="margin-top:6px;">
              <div style="font-size:12px; color:var(--app-muted); margin-bottom:4px;">选择合作项目并发送邀请</div>
              <el-select
                v-model="selectedPostId"
                size="small"
                placeholder="请选择一个你的项目"
                style="width:100%; margin-bottom:6px;"
              >
                <el-option
                  v-for="p in myPosts"
                  :key="p.id"
                  :label="p.title"
                  :value="p.id"
                />
              </el-select>
              <div v-if="currentRequest" style="font-size:12px; margin-bottom:6px;">
                当前状态：
                <span class="pill" :class="statusClass(currentRequest)" style="font-size:11px;">
                  {{ statusLabel(currentRequest) }}
                </span>
              </div>
              <div v-if="currentRequest" style="font-size:12px; color:var(--app-muted); margin-bottom:6px;">
                该项目已向该学生发起过合作流程，无需再次发送邀请。
              </div>
            </div>
            <div style="margin-top:6px; display:flex; gap:8px;">
              <el-button
                type="primary"
                size="small"
                :disabled="!selectedPostId || !canInvite"
                @click="invite(selectedStudent)"
              >
                发出合作邀请
              </el-button>
              <el-button size="small" @click="chat(selectedStudent)">发私信</el-button>
            </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 邀请弹窗 -->
    <el-dialog v-model="inviteDialogVisible" title="发送合作邀请" width="480px">
      <div v-if="selectedStudent" style="margin-bottom: 16px;">
        <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px;">
          邀请 {{ selectedStudent.user.display_name }} 加入项目
        </div>
        <div v-if="selectedProjectInfo?.required_roles?.length" style="margin-bottom: 12px;">
          <div style="font-size: 12px; color: var(--app-muted); margin-bottom: 4px;">项目招募角色：</div>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            <el-tag v-for="role in selectedProjectInfo.required_roles" :key="role" size="small" type="info">
              {{ role }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <el-form label-position="top" size="small">
        <el-form-item label="建议角色（可选）">
          <RoleTagSelector
            v-model="inviteForm.suggested_roles"
            hint="选择您建议该学生在项目中承担的角色"
            add-button-text="添加角色"
            :suggested-tags="selectedProjectInfo?.required_roles || []"
            :max-tags="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div style="text-align: right;">
          <el-button size="small" @click="inviteDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="submitInvite">发送邀请</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import { Folder } from '@element-plus/icons-vue';
import RoleTagSelector from "../../components/RoleTagSelector.vue";


const students = ref<any[]>([]);
const filters = reactive({ keyword: "", grade: "" });
const page = ref(1);
const pageSize = ref(4);
const selectedStudent = ref<any | null>(null);
const myPosts = ref<any[]>([]);
const selectedPostId = ref<number | null>(null);
const currentRequest = ref<any | null>(null);
const recommendScores = reactive<Record<number, number>>({});

// 项目选择器相关
const myProjects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

// 邀请弹窗相关
const inviteDialogVisible = ref(false);
const inviteForm = reactive({
  suggested_roles: [] as string[]
});

// 获取选中项目的信息
const selectedProjectInfo = computed(() => {
  if (!selectedPostId.value) return null;
  return myPosts.value.find(p => p.id === selectedPostId.value);
});

const canInvite = computed(() => {
  if (!selectedPostId.value) return false;
  return currentRequest.value == null;
});


async function load() {
  page.value = 1;
  const params: any = {
    keyword: filters.keyword || undefined,
    grade: filters.grade || undefined
  };
  
  // 不使用project_id筛选，而是获取所有学生
  const resp = await axios.get("/api/students", { params });
  students.value = resp.data.items;
  
  // 如果选择了项目，根据项目计算匹配度并排序
  if (selectedProjectId.value) {
    await calculateProjectMatchScores(selectedProjectId.value);
    // 按匹配度降序排序
    students.value.sort((a, b) => {
      const scoreA = recommendScores[a.user.id] || 0;
      const scoreB = recommendScores[b.user.id] || 0;
      return scoreB - scoreA;
    });
  }
  
  if (!selectedStudent.value && students.value.length) {
    selectedStudent.value = students.value[0];
  }
  const meResp = await axios.get("/api/auth/me");
  const postsResp = await axios.get("/api/teacher-posts");
  myPosts.value = (postsResp.data.items || []).filter((x: any) => x.teacher && x.teacher.id === meResp.data.id);
  
  // 加载教师的项目列表用于选择器
  myProjects.value = myPosts.value;
  if (!selectedPostId.value && myPosts.value.length) {
    selectedPostId.value = myPosts.value[0].id;
  }
  await loadCurrentRequest();

  // 如果没有选择项目，使用通用推荐
  if (!selectedProjectId.value) {
    const matchResp = await axios.get("/api/match/top", { params: { limit: 50 } });
    Object.keys(recommendScores).forEach(k => delete recommendScores[Number(k)]);
    if (matchResp.data.kind === "students") {
      (matchResp.data.items || []).forEach((r: any) => {
        if (r.user_id) {
          recommendScores[r.user_id] = r.score || 0;
        }
      });
    }
  }
}

// 根据项目计算学生匹配度
async function calculateProjectMatchScores(projectId: number) {
  // 清空现有分数
  Object.keys(recommendScores).forEach(k => delete recommendScores[Number(k)]);
  
  // 获取项目信息
  const project = myProjects.value.find(p => p.id === projectId);
  if (!project) return;
  
  // 提取项目的技术栈和标签
  const projectTags = [...(project.tech_stack || []), ...(project.tags || [])];
  
  // 为每个学生计算匹配度
  students.value.forEach(student => {
    const studentSkills = (student.skills || []).map((s: any) => s.name);
    const studentInterests = student.interests || [];
    const studentTags = [...studentSkills, ...studentInterests];
    
    // 计算交集
    const intersection = projectTags.filter(tag => 
      studentTags.some(st => st.toLowerCase().includes(tag.toLowerCase()) || tag.toLowerCase().includes(st.toLowerCase()))
    );
    
    // 计算匹配度（0-1之间）
    const score = projectTags.length > 0 ? intersection.length / projectTags.length : 0;
    recommendScores[student.user.id] = score;
  });
}


const sortedStudents = computed(() => {
  return [...students.value].sort((a, b) => {
    const sa = recommendScores[a.user.id] || 0;
    const sb = recommendScores[b.user.id] || 0;
    if (sb !== sa) return sb - sa;
    return (b.weekly_hours || 0) - (a.weekly_hours || 0);
  });
});


const totalStudents = computed(() => sortedStudents.value.length);


const pagedStudents = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return sortedStudents.value.slice(start, start + pageSize.value);
});


function handlePageChange(p: number) {
  page.value = p;
}

// 处理项目选择变化
function handleProjectChange() {
  load();
}


async function invite(s: any) {
  if (!selectedPostId.value) return;
  if (!canInvite.value) return;
  
  // 打开邀请弹窗
  inviteForm.suggested_roles = [];
  inviteDialogVisible.value = true;
}


// 提交邀请
async function submitInvite() {
  if (!selectedStudent.value || !selectedPostId.value) return;
  
  try {
    await axios.post("/api/cooperation/request", {
      post_id: selectedPostId.value,
      student_user_id: selectedStudent.value.user.id,
      suggested_roles: inviteForm.suggested_roles
    });
    await loadCurrentRequest();
    inviteDialogVisible.value = false;
    ElMessage.success("已发送合作邀请，等待学生确认");
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || "邀请失败，请重试");
  }
}


async function chat(s: any) {
  const me = await axios.get("/api/auth/me");
  await axios.post("/api/messages/send", {
    teacher_user_id: me.data.id,
    student_user_id: s.user.id,
    content: "你好，我对你的技能很感兴趣，方便进一步交流吗？"
  });
  ElMessage.success("已发送一条私信");
}


function select(row: any) {
  selectedStudent.value = row;
  loadCurrentRequest();
}


watch(selectedPostId, () => {
  loadCurrentRequest();
});


async function loadCurrentRequest() {
  if (!selectedStudent.value || !selectedPostId.value) {
    currentRequest.value = null;
    return;
  }
  const resp = await axios.get("/api/cooperation/requests", {
    params: { post_id: selectedPostId.value }
  });
  const items = resp.data.items || [];
  const found = items.find((r: any) => r.student && r.student.id === selectedStudent.value.user.id);
  currentRequest.value = found || null;
}


function statusLabel(r: any) {
  if (r.final_status === "confirmed") return "已确认";
  if (r.final_status === "rejected") return "已拒绝";
  if (r.teacher_status === "accepted" && r.student_status === "accepted") return "待确认";
  if (r.teacher_status === "accepted" && r.student_status === "pending") return "待学生接受";
  if (r.teacher_status === "pending" && r.student_status === "accepted") return "待教师确认";
  if (r.teacher_status === "accepted") return "老师已接受";
  if (r.student_status === "accepted") return "学生已接受";
  return "待处理";
}


function statusClass(r: any) {
  if (r.final_status === "confirmed") return "badge-green";
  if (r.final_status === "rejected") return "badge-amber";
  return "badge-blue";
}


function scoreClass(score: number) {
  if (score >= 85) return "badge-green";
  if (score >= 70) return "badge-blue";
  if (score >= 55) return "badge-amber";
  return "badge-gray";
}


async function downloadResume(file: any) {
  if (!file || !file.id) return;
  const resp = await axios.get(`/api/files/${file.id}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.original_name || "resume";
  a.click();
  window.URL.revokeObjectURL(url);
}


onMounted(() => {
  load();
});
</script>

<style scoped>
.ts-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ts-main {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
  overflow: hidden;
}

.ts-main :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.ts-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ts-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.list-wrap {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.table-wrap {
  flex: 1 1 auto;
  min-height: 0;
}

.pager {
  margin-top: 8px;
  text-align: right;
  flex: 0 0 auto;
}

.detail-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
