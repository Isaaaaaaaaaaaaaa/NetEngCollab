<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">项目与竞赛管理</h2>
        <p class="page-subtitle">选择项目查看详细信息与学生选择情况</p>
      </div>
      <el-space :size="8">
        <el-select v-model="filters.post_type" size="small" style="width: 140px;">
          <el-option label="全部类型" value="" />
          <el-option label="科研项目" value="project" />
          <el-option label="大创项目" value="innovation" />
          <el-option label="学科竞赛" value="competition" />
        </el-select>
        <el-button size="small" @click="load">筛选</el-button>
        <el-button size="small" type="primary" @click="createVisible = true">发布新项目</el-button>
      </el-space>
    </div>

    <div v-if="hint" style="font-size: 11px; color: #16a34a; margin-top: 6px;">已发布</div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="7">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">我的项目</div>
          </template>
          <el-empty v-if="!posts.length" description="暂无记录" />
          <el-scrollbar v-else style="max-height: 320px;">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="p in posts"
                :key="p.id"
                style="padding:6px 8px; border-radius:8px; cursor:pointer; display:flex; flex-direction:column; gap:2px;"
                :style="p.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="selectPost(p.id)"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
                  <span class="truncate" style="max-width:160px; font-weight:500;">{{ p.title }}</span>
                  <span class="pill" :class="p.post_type === 'competition' ? 'badge-amber' : 'badge-blue'">
                    {{ typeLabel(p.post_type) }}
                  </span>
                </div>
                <div style="font-size:11px; color:var(--app-muted);">
                  已选择 {{ requestSummary[p.id]?.count || 0 }} 人
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="17">
        <el-row :gutter="12">
          <el-col :xs="24" :lg="14">
            <el-card class="app-card" shadow="never">
              <template #header>
                <div class="page-subtitle">项目详情</div>
              </template>
              <div v-if="!selectedPost" style="font-size:12px; color:var(--app-muted);">
                在左侧列表中选择一个项目查看详细信息。
              </div>
              <div v-else style="font-size:13px; display:flex; flex-direction:column; gap:6px;">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                  <div style="font-size:15px; font-weight:600;" class="truncate">{{ selectedPost.title }}</div>
                  <el-button size="small" type="primary" text @click="openEdit(selectedPost)">编辑</el-button>
                </div>
                <div>
                  类型：
                  <span class="pill" :class="selectedPost.post_type === 'competition' ? 'badge-amber' : 'badge-blue'">
                    {{ typeLabel(selectedPost.post_type) }}
                  </span>
                </div>
                <div>简介：{{ selectedPost.content }}</div>
                <div>
                  技术栈：
                  <span v-if="!selectedPost.tech_stack?.length" style="color:var(--app-muted);">未设置</span>
                </div>
                <div v-if="selectedPost.tech_stack?.length" style="display:flex; flex-wrap:wrap; gap:4px;">
                  <span v-for="t in selectedPost.tech_stack" :key="t" class="tag">{{ t }}</span>
                  <span v-for="t in selectedPost.tags" :key="t" class="tag">{{ t }}</span>
                </div>
                <div>招募人数：{{ selectedPost.recruit_count || '未设置' }}</div>
                <div>项目周期：{{ selectedPost.duration || '未设置' }}</div>
                <div>预期成果与要求：{{ selectedPost.outcome || '未填写' }}</div>
                <div>联系方式：{{ selectedPost.contact || '未填写' }}</div>
                <div>
                  报名截止时间：
                  {{ selectedPost.deadline ? selectedPost.deadline.slice(0, 10) : '未设置' }}
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="10">
            <el-card class="app-card" shadow="never">
              <template #header>
                <div class="page-subtitle">选择该项目的学生</div>
              </template>
              <el-empty v-if="!selectedStudents.length" description="暂无学生选择该项目" />
              <el-scrollbar v-else style="max-height: 260px;">
                <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
                  <li
                    v-for="r in selectedStudents"
                    :key="r.id"
                    style="padding:4px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
                  >
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
                      <span class="truncate" style="max-width:130px;">{{ r.student?.display_name || '学生' }}</span>
                      <div style="display:flex; align-items:center; gap:4px;">
                        <span class="pill" :class="statusClass(r)" style="font-size:11px;">
                          {{ statusLabel(r) }}
                        </span>
                        <el-button
                          v-if="r.teacher_status === 'pending' && r.final_status === 'pending'"
                          size="small"
                          type="primary"
                          text
                          @click="acceptStudent(r)"
                        >
                          同意
                        </el-button>
                      </div>
                    </div>
                  </li>
                </ul>
              </el-scrollbar>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-dialog v-model="createVisible" title="发布新项目" width="640px">
      <el-form :model="form" label-position="top" size="small">
        <el-form-item label="项目类型">
          <el-select v-model="form.post_type">
            <el-option label="科研项目" value="project" />
            <el-option label="大创项目" value="innovation" />
            <el-option label="学科竞赛" value="competition" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="标题" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="简要介绍研究内容、技术栈、预期成果"
          />
        </el-form-item>
        <el-form-item label="技术栈（逗号分隔）">
          <el-input v-model="form.tech_stack" placeholder="如：Python, 深度学习" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="form.tags" placeholder="如：网络安全, 目标检测" />
        </el-form-item>
        <el-form-item label="招募人数">
          <el-input-number v-model="form.recruit_count" :min="1" :max="99" controls-position="right" />
        </el-form-item>
        <el-form-item label="立项书 / 往期成果附件">
          <input ref="attachmentInput" type="file" style="display:none" @change="onSelectAttachment" />
          <el-button size="small" @click="triggerAttachment">选择文件</el-button>
          <span v-if="attachmentName" class="truncate" style="font-size:11px; margin-left:6px;">{{ attachmentName }}</span>
        </el-form-item>
        <el-form-item label="项目周期">
          <el-input v-model="form.duration" placeholder="如：1 学期，3 个月" />
        </el-form-item>
        <el-form-item label="预期成果与要求">
          <el-input v-model="form.outcome" type="textarea" :rows="3" placeholder="如：论文、比赛奖项、开源项目等" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact" placeholder="如：邮箱、企业微信等" />
        </el-form-item>
        <el-form-item label="报名截止时间">
          <el-date-picker
            v-model="form.deadline"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="createVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="publish">发布</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑项目信息" width="520px">
      <el-form :model="editForm" label-position="top" size="small">
        <el-form-item label="项目类型">
          <el-select v-model="editForm.post_type">
            <el-option label="科研项目" value="project" />
            <el-option label="大创项目" value="innovation" />
            <el-option label="学科竞赛" value="competition" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input v-model="editForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="技术栈（逗号分隔）">
          <el-input v-model="editForm.tech_stack" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="editForm.tags" />
        </el-form-item>
        <el-form-item label="招募人数">
          <el-input-number v-model="editForm.recruit_count" :min="1" :max="99" controls-position="right" />
        </el-form-item>
        <el-form-item label="立项书 / 往期成果附件">
          <input ref="editAttachmentInput" type="file" style="display:none" @change="onSelectEditAttachment" />
          <el-button size="small" @click="triggerEditAttachment">重新上传附件</el-button>
          <span v-if="editAttachmentName" class="truncate" style="font-size:11px; margin-left:6px;">{{ editAttachmentName }}</span>
        </el-form-item>
        <el-form-item label="项目周期">
          <el-input v-model="editForm.duration" />
        </el-form-item>
        <el-form-item label="预期成果与要求">
          <el-input v-model="editForm.outcome" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="editForm.contact" />
        </el-form-item>
        <el-form-item label="报名截止时间">
          <el-date-picker
            v-model="editForm.deadline"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="editVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";


const posts = ref<any[]>([]);
const filters = reactive({ post_type: "" });
const hint = ref(false);
const createVisible = ref(false);
const editVisible = ref(false);
const editing = ref<any | null>(null);
const attachmentInput = ref<HTMLInputElement | null>(null);
const editAttachmentInput = ref<HTMLInputElement | null>(null);
const attachmentName = ref("");
const editAttachmentName = ref("");
const selectedId = ref<number | null>(null);
const selectedStudents = ref<any[]>([]);
const requestSummary = reactive<Record<number, { count: number }>>({});

const form = reactive({
  post_type: "project",
  title: "",
  content: "",
  tech_stack: "",
  tags: "",
  recruit_count: null as number | null,
  duration: "",
  outcome: "",
  contact: "",
  deadline: "",
  attachment_file_id: null as number | null
});

const editForm = reactive({
  id: 0,
  post_type: "project",
  title: "",
  content: "",
  tech_stack: "",
  tags: "",
  recruit_count: null as number | null,
  duration: "",
  outcome: "",
  contact: "",
  deadline: "",
  attachment_file_id: null as number | null
});


const selectedPost = computed(() => posts.value.find(p => p.id === selectedId.value) || null);


function typeLabel(t: string) {
  if (t === "competition") return "学科竞赛";
  if (t === "innovation") return "大创项目";
  return "科研项目";
}


function triggerAttachment() {
  if (attachmentInput.value) {
    attachmentInput.value.click();
  }
}


function triggerEditAttachment() {
  if (editAttachmentInput.value) {
    editAttachmentInput.value.click();
  }
}


async function onSelectAttachment(e: Event) {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const fd = new FormData();
  fd.append("file", target.files[0]);
  const fileResp = await axios.post("/api/files", fd, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  form.attachment_file_id = fileResp.data.file_id;
  attachmentName.value = target.files[0].name;
}


async function onSelectEditAttachment(e: Event) {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const fd = new FormData();
  fd.append("file", target.files[0]);
  const fileResp = await axios.post("/api/files", fd, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  editForm.attachment_file_id = fileResp.data.file_id;
  editAttachmentName.value = target.files[0].name;
}


async function load() {
  const meResp = await axios.get("/api/auth/me");
  const resp = await axios.get("/api/teacher-posts", {
    params: { post_type: filters.post_type || undefined }
  });
  posts.value = (resp.data.items || []).filter((x: any) => x.teacher && x.teacher.id === meResp.data.id);
  if (posts.value.length && !selectedId.value) {
    selectedId.value = posts.value[0].id;
  }
  await loadRequests();
}


async function publish() {
  if (!form.title || !form.content) return;
  await axios.post("/api/teacher-posts", {
    ...form,
    tech_stack: form.tech_stack
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x),
    tags: form.tags
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x)
  });
  hint.value = true;
  setTimeout(() => {
    hint.value = false;
  }, 3000);
  createVisible.value = false;
  attachmentName.value = "";
  form.title = "";
  form.content = "";
  form.tech_stack = "";
  form.tags = "";
  form.recruit_count = null;
  form.duration = "";
  form.outcome = "";
  form.contact = "";
  form.deadline = "";
  form.attachment_file_id = null;
  await load();
}


function openEdit(row: any) {
  editing.value = row;
  editForm.id = row.id;
  editForm.post_type = row.post_type;
  editForm.title = row.title;
  editForm.content = row.content;
  editForm.tech_stack = (row.tech_stack || []).join(", ");
  editForm.tags = (row.tags || []).join(", ");
  editForm.recruit_count = row.recruit_count || null;
  editForm.duration = row.duration || "";
  editForm.outcome = row.outcome || "";
  editForm.contact = row.contact || "";
  editForm.deadline = row.deadline ? row.deadline.slice(0, 10) : "";
  editForm.attachment_file_id = row.attachment_file_id || null;
  attachmentName.value = "";
  editAttachmentName.value = "";
  editVisible.value = true;
}


async function saveEdit() {
  if (!editForm.title || !editForm.content) return;
  await axios.put(`/api/teacher-posts/${editForm.id}`, {
    post_type: editForm.post_type,
    title: editForm.title,
    content: editForm.content,
    tech_stack: editForm.tech_stack
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x),
    tags: editForm.tags
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x),
    recruit_count: editForm.recruit_count,
    duration: editForm.duration,
    outcome: editForm.outcome,
    contact: editForm.contact,
    deadline: editForm.deadline || null,
    attachment_file_id: editForm.attachment_file_id
  });
  editVisible.value = false;
  await load();
}


async function loadRequests() {
  if (!selectedId.value) {
    selectedStudents.value = [];
    return;
  }
  const resp = await axios.get("/api/cooperation/requests", {
    params: { post_id: selectedId.value }
  });
  const items = resp.data.items || [];
  selectedStudents.value = items;
  Object.keys(requestSummary).forEach(k => delete requestSummary[Number(k)]);
  items.forEach((r: any) => {
    const pid = r.post?.id;
    if (!pid) return;
    if (!requestSummary[pid]) {
      requestSummary[pid] = { count: 0 };
    }
    requestSummary[pid].count += 1;
  });
}


function selectPost(id: number) {
  selectedId.value = id;
  loadRequests();
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


async function acceptStudent(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "accept" });
  await loadRequests();
}


onMounted(() => {
  load();
});
</script>
