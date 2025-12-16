<template>
  <div class="page split-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">{{ mode === "resources" ? "科研 / 竞赛资源库" : "成果展示" }}</h2>
        <p class="page-subtitle">
          {{ mode === "resources" ? "按方向、类型和标签快速查找资料" : "展示已完成项目的论文、专利、获奖与演示" }}
        </p>
      </div>
      <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-end;">
        <el-radio-group v-model="mode" size="small">
          <el-radio-button label="resources">资源库</el-radio-button>
          <el-radio-button label="achievements">成果展示</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="reactFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="liked">我点赞的</el-radio-button>
          <el-radio-button label="favorited">我收藏的</el-radio-button>
        </el-radio-group>
        <el-space :size="8">
          <el-input
            v-model="filters.keyword"
            size="small"
            :placeholder="mode === 'resources' ? '关键词，如 Transformer' : '关键词，如 蓝桥杯 一等奖'"
            style="width: 240px;"
            clearable
          />
          <el-button size="small" type="primary" plain @click="load">检索</el-button>
        </el-space>
      </div>
    </div>

    <el-row :gutter="16" class="split-row" style="margin-top: 6px;">
      <el-col :xs="24" :lg="16">
        <el-card class="app-card split-card" shadow="never">
          <template #header>
            <div class="page-subtitle">{{ mode === "resources" ? "资源列表" : "成果列表" }}</div>
          </template>
          <el-empty v-if="!items.length" :description="mode === 'resources' ? '暂无资源记录' : '暂无成果记录'" />
          <el-scrollbar v-else class="split-scroll">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="r in items"
                :key="r.id"
                style="padding:10px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:4px;">
                  <div style="display:flex; flex-direction:column; gap:2px; min-width:0;">
                    <span class="truncate" style="font-size:13px; font-weight:600; max-width:420px;">{{ r.title }}</span>
                    <span class="truncate" style="font-size:11px; color:var(--app-muted); max-width:420px;">{{ r.description || "无描述" }}</span>
                  </div>
                  <span class="pill badge-blue" style="font-size:10px;">{{ r.resource_type }}</span>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                  <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span v-for="t in r.tags" :key="t" class="tag">{{ t }}</span>
                  </div>
                  <div style="display:flex; gap:8px; align-items:center; font-size:11px; color:var(--app-muted);">
                    <span>{{ r.uploader?.display_name || "未知" }}</span>
                    <span>{{ r.created_at?.slice(0, 10) }}</span>
                    <el-button size="small" text type="primary" @click="download(r)">下载</el-button>
                  </div>
                </div>
                <div style="margin-top:6px;">
                  <InteractionsPanel
                    :target-type="'resource'"
                    :target-id="r.id"
                    @changed="handleInteractionChanged"
                  />
                </div>
              </li>
            </ul>
          </el-scrollbar>
          <div v-if="total > pageSize" style="margin-top:8px; text-align:right;">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="page"
              :page-size="pageSize"
              :total="total"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="app-card split-card" shadow="never">
          <template #header>
            <div class="page-subtitle">{{ mode === "resources" ? "上传资源" : "上传成果" }}</div>
          </template>
          <el-scrollbar class="split-scroll">
            <div style="padding-right: 8px;">
              <el-form :model="upload" label-position="top" size="small">
                <el-form-item label="资源类型">
                  <el-select v-model="upload.resource_type">
                    <el-option label="科研论文" value="paper" />
                    <el-option label="数据集" value="dataset" />
                    <el-option label="讲座 / 分享" value="slides" />
                    <el-option label="项目成果" value="project" />
                    <el-option label="获奖证书" value="award" />
                    <el-option label="专利 / 软件著作" value="patent" />
                  </el-select>
                </el-form-item>
                <el-form-item :label="mode === 'resources' ? '资源标题' : '成果标题'">
                  <el-input v-model="upload.title" :placeholder="mode === 'resources' ? '资源标题' : '成果标题'" />
                </el-form-item>
                <el-form-item :label="mode === 'resources' ? '资源简介' : '成果简介'">
                  <el-input
                    v-model="upload.description"
                    type="textarea"
                    :rows="3"
                    :placeholder="mode === 'resources' ? '简要说明资源内容与使用场景' : '简要说明成果背景与亮点'"
                  />
                </el-form-item>
                <el-form-item label="标签（逗号分隔）">
                  <el-input
                    v-model="upload.tags"
                    :placeholder="mode === 'resources' ? '如：CV, 比赛经验' : '如：国赛一等奖, 校级大创'"
                  />
                </el-form-item>
                <el-form-item label="选择文件">
                  <input ref="fileInput" type="file" style="font-size:11px; color:var(--app-muted);" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" style="width: 100%;" @click="doUpload">提交</el-button>
                </el-form-item>
              </el-form>
              <div v-if="hint" style="font-size: 11px; color: #16a34a;">已提交，待管理员审核通过后对全平台可见。</div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import axios from "axios";
import InteractionsPanel from "../../components/InteractionsPanel.vue";


const items = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const mode = ref<"resources" | "achievements">("resources");
const reactFilter = ref<"all" | "liked" | "favorited">("all");
const page = ref(1);
const pageSize = ref(5);
const total = ref(0);
const upload = reactive({
  resource_type: "paper",
  title: "",
  description: "",
  tags: ""
});
const fileInput = ref<HTMLInputElement | null>(null);
const hint = ref(false);
async function load() {
  const resp = await axios.get("/api/resources", {
    params: {
      keyword: filters.keyword || undefined,
      category: mode.value === "achievements" ? "成果" : undefined,
      like_only: reactFilter.value === "liked" ? 1 : undefined,
      favorite_only: reactFilter.value === "favorited" ? 1 : undefined,
      page: page.value,
      page_size: pageSize.value
    }
  });
  items.value = resp.data.items;
  total.value = resp.data.total || 0;
}


async function download(r: any) {
  if (!r.file) return;
  const resp = await axios.get(`/api/files/${r.file.id}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = r.file.original_name;
  a.click();
  window.URL.revokeObjectURL(url);
}


async function doUpload() {
  if (!upload.title || !fileInput.value || !fileInput.value.files || !fileInput.value.files[0]) return;
  const fd = new FormData();
  fd.append("file", fileInput.value.files[0]);
  const fileResp = await axios.post("/api/files", fd, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  await axios.post("/api/resources", {
    resource_type: upload.resource_type,
    title: upload.title,
    description: upload.description,
    tags: upload.tags
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x),
    file_id: fileResp.data.file_id,
    category: mode.value === "achievements" ? "成果" : undefined
  });
  hint.value = true;
  setTimeout(() => {
    hint.value = false;
  }, 3000);
  await load();
}


function handleInteractionChanged() {
  if (reactFilter.value !== "all") {
    load();
  }
}


function handlePageChange(p: number) {
  page.value = p;
  load();
}


watch(mode, () => {
  page.value = 1;
  load();
});


watch(reactFilter, () => {
  page.value = 1;
  load();
});


onMounted(() => {
  load();
});
</script>

<style scoped>
.split-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.split-row {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
  overflow: hidden;
}

.split-row :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.split-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.split-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.split-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
