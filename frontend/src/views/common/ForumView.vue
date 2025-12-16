<template>
  <div class="page split-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">话题讨论区</h2>
        <p class="page-subtitle">按研究方向与竞赛类型划分的板块交流空间</p>
      </div>
      <el-space :size="8">
        <el-radio-group v-model="reactFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="liked">我点赞的</el-radio-button>
          <el-radio-button label="favorited">我收藏的</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="filters.keyword"
          size="small"
          placeholder="关键词，如 CNN"
          style="width: 220px;"
          clearable
        />
        <el-button size="small" type="primary" plain @click="load">检索</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" class="split-row" style="margin-top: 6px;">
      <el-col :xs="24" :lg="16">
        <el-card class="app-card split-card" shadow="never">
          <template #header>
            <div class="page-subtitle">话题列表</div>
          </template>
          <el-empty v-if="!topics.length" description="暂无话题" />
          <el-scrollbar v-else class="split-scroll">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="t in topics"
                :key="t.id"
                style="padding:8px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
                >
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
                  <span class="truncate" style="max-width:220px; font-weight:500;">{{ t.title }}</span>
                  <span class="pill badge-blue" style="font-size:10px;">{{ t.category }}</span>
                </div>
                <div style="font-size:12px; color:var(--app-muted); margin-bottom:4px;" class="truncate">
                  {{ t.content }}
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                  <span v-for="tag in t.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
                <div style="margin-top:4px;">
                  <InteractionsPanel :target-type="'forum_topic'" :target-id="t.id" />
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
            <div class="page-subtitle">发起话题</div>
          </template>
          <el-scrollbar class="split-scroll">
            <div style="padding-right: 8px;">
              <el-form :model="form" label-position="top" size="small">
                <el-form-item label="板块">
                  <el-select v-model="form.category">
                    <el-option label="机器学习讨论区" value="机器学习" />
                    <el-option label="网络安全讨论区" value="网络安全" />
                    <el-option label="ACM 竞赛交流区" value="ACM" />
                    <el-option label="综合讨论" value="综合" />
                  </el-select>
                </el-form-item>
                <el-form-item label="话题标题">
                  <el-input v-model="form.title" placeholder="话题标题" />
                </el-form-item>
                <el-form-item label="内容">
                  <el-input
                    v-model="form.content"
                    type="textarea"
                    :rows="4"
                    placeholder="描述你的问题、经验或观点"
                  />
                </el-form-item>
                <el-form-item label="标签（逗号分隔）">
                  <el-input v-model="form.tags" placeholder="如：CV, 算法, 备赛经验" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" style="width:100%;" @click="publish">发布话题</el-button>
                </el-form-item>
              </el-form>
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


const topics = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const reactFilter = ref<"all" | "liked" | "favorited">("all");
const page = ref(1);
const pageSize = ref(5);
const total = ref(0);
const form = reactive({
  category: "机器学习",
  title: "",
  content: "",
  tags: ""
});


async function load() {
  const resp = await axios.get("/api/forum/topics", {
    params: {
      keyword: filters.keyword || undefined,
      like_only: reactFilter.value === "liked" ? 1 : undefined,
      favorite_only: reactFilter.value === "favorited" ? 1 : undefined,
      page: page.value,
      page_size: pageSize.value
    }
  });
  topics.value = resp.data.items;
  total.value = resp.data.total || 0;
}


async function publish() {
  if (!form.title || !form.content) return;
  await axios.post("/api/forum/topics", {
    category: form.category,
    title: form.title,
    content: form.content,
    tags: form.tags
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x)
  });
  form.title = "";
  form.content = "";
  form.tags = "";
  await load();
}


function handlePageChange(p: number) {
  page.value = p;
  load();
}


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
