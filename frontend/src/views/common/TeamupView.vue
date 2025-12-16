<template>
  <div class="page split-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">组队互助区</h2>
        <p class="page-subtitle">快速寻找缺前端 / 算法 / 后端等角色的队伍</p>
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
          placeholder="关键词，如 前端"
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
            <div class="page-subtitle">组队需求</div>
          </template>
          <el-scrollbar class="split-scroll">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="p in itemsDisplay"
                :key="p.id"
                style="padding:8px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
                  <span class="truncate" style="max-width:220px; font-weight:500;">{{ p.__placeholder ? "暂无" : p.title }}</span>
                  <span v-if="!p.__placeholder" class="pill badge-amber" style="font-size:10px;">{{ p.post_kind }}</span>
                  <span v-else style="font-size:11px; color:var(--app-muted);">-</span>
                </div>
                <div style="font-size:12px; color:var(--app-muted); margin-bottom:4px;" class="truncate">
                  {{ p.__placeholder ? "-" : p.content }}
                </div>
                <div v-if="!p.__placeholder" style="display:flex; flex-wrap:wrap; gap:4px;">
                  <span v-for="r in p.needed_roles" :key="r" class="tag">{{ r }}</span>
                </div>
                <div v-if="!p.__placeholder" style="margin-top:4px;">
                  <InteractionsPanel :target-type="'teamup_post'" :target-id="p.id" />
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
            <div class="page-subtitle">发布需求</div>
          </template>
          <el-scrollbar class="split-scroll">
            <div style="padding-right: 8px;">
              <el-form :model="form" label-position="top" size="small">
                <el-form-item label="需求类型">
                  <el-select v-model="form.post_kind">
                    <el-option label="竞赛组队" value="竞赛组队" />
                    <el-option label="科研分工" value="科研分工" />
                    <el-option label="短期互助" value="短期互助" />
                  </el-select>
                </el-form-item>
                <el-form-item label="标题">
                  <el-input v-model="form.title" placeholder="标题，如 缺前端开发" />
                </el-form-item>
                <el-form-item label="需求描述">
                  <el-input
                    v-model="form.content"
                    type="textarea"
                    :rows="4"
                    placeholder="说明当前队伍情况、缺失角色和时间安排"
                  />
                </el-form-item>
                <el-form-item label="需要的角色（逗号分隔）">
                  <el-input v-model="form.needed_roles" placeholder="如：前端, 算法" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" style="width:100%;" @click="publish">发布</el-button>
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
import { computed, onMounted, reactive, ref, watch } from "vue";
import axios from "axios";
import InteractionsPanel from "../../components/InteractionsPanel.vue";


const items = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const reactFilter = ref<"all" | "liked" | "favorited">("all");
const page = ref(1);
const pageSize = ref(5);
const total = ref(0);
const form = reactive({
  post_kind: "竞赛组队",
  title: "",
  content: "",
  needed_roles: ""
});


const itemsDisplay = computed(() => {
  const out: any[] = (items.value || []).map((p: any) => ({ ...p, __placeholder: false }));
  const target = pageSize.value;
  for (let i = out.length; i < target; i++) {
    out.push({ id: `ph-${page.value}-${i}`, __placeholder: true });
  }
  return out;
});


async function load() {
  const resp = await axios.get("/api/teamup", {
    params: {
      keyword: filters.keyword || undefined,
      like_only: reactFilter.value === "liked" ? 1 : undefined,
      favorite_only: reactFilter.value === "favorited" ? 1 : undefined,
      page: page.value,
      page_size: pageSize.value
    }
  });
  items.value = resp.data.items;
  total.value = resp.data.total || 0;
}


async function publish() {
  if (!form.title || !form.content) return;
  await axios.post("/api/teamup", {
    post_kind: form.post_kind,
    title: form.title,
    content: form.content,
    needed_roles: form.needed_roles
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x)
  });
  form.title = "";
  form.content = "";
  form.needed_roles = "";
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
