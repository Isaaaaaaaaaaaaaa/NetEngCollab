<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">平台数据分析</h2>
        <p class="page-subtitle">查看活跃度、热门方向与竞赛参与趋势</p>
      </div>
    </div>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">平台活跃度（最近 14 天）</div>
      </template>
      <div v-if="!activity.posts_daily.length && !activity.messages_daily.length" style="font-size:12px; color:var(--app-muted);">
        暂无活跃度数据。
      </div>
      <div v-else style="border:1px solid rgba(148,163,184,0.25); border-radius:12px; padding:12px; background:linear-gradient(180deg, rgba(59,130,246,0.06), rgba(255,255,255,0));">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
          <div style="display:flex; gap:10px; align-items:center; font-size:12px; color:var(--app-muted);">
            <span style="display:inline-flex; align-items:center; gap:6px;">
              <span style="width:10px; height:10px; border-radius:999px; background:#3b82f6;"></span>
              发布量
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px;">
              <span style="width:10px; height:10px; border-radius:999px; background:#22c55e;"></span>
              沟通量
            </span>
          </div>
          <div style="font-size:11px; color:var(--app-muted);">{{ activity.posts_daily?.[0]?.date?.slice(5) }} - {{ activity.posts_daily?.[activity.posts_daily.length - 1]?.date?.slice(5) }}</div>
        </div>
        <svg :viewBox="`0 0 ${activityChart.w} ${activityChart.h}`" :width="'100%'" :height="140" style="display:block;">
          <defs>
            <linearGradient id="gradPosts" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.28" />
              <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
            </linearGradient>
            <linearGradient id="gradMsgs" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#22c55e" stop-opacity="0.22" />
              <stop offset="100%" stop-color="#22c55e" stop-opacity="0" />
            </linearGradient>
          </defs>

          <g opacity="0.35">
            <line
              v-for="x in activityChart.gridX"
              :key="x"
              :x1="x"
              :x2="x"
              :y1="activityChart.padT"
              :y2="activityChart.h - activityChart.padB"
              stroke="#94a3b8"
              stroke-width="1"
              stroke-dasharray="3 6"
            />
            <line
              v-for="y in activityChart.gridY"
              :key="y"
              :y1="y"
              :y2="y"
              :x1="activityChart.padL"
              :x2="activityChart.w - activityChart.padR"
              stroke="#94a3b8"
              stroke-width="1"
              stroke-dasharray="3 6"
            />
          </g>

          <path :d="postsArea" fill="url(#gradPosts)" />
          <path :d="msgsArea" fill="url(#gradMsgs)" />

          <path :d="postsPath" fill="none" stroke="#3b82f6" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
          <path :d="msgsPath" fill="none" stroke="#22c55e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />

          <g>
            <circle v-for="p in postsDots" :key="`p-${p.x}`" :cx="p.x" :cy="p.y" r="2.6" fill="#3b82f6" />
            <circle v-for="p in msgsDots" :key="`m-${p.x}`" :cx="p.x" :cy="p.y" r="2.6" fill="#22c55e" />
          </g>
        </svg>
      </div>
      <div style="margin-top:8px; font-size:11px; color:var(--app-muted);">
        {{ activityConclusion }}
      </div>
    </el-card>

    <el-row :gutter="16" class="an-row" style="margin-top:16px;">
      <el-col :xs="24" :lg="12">
        <el-card class="app-card an-card" shadow="never">
          <template #header>
            <div class="page-subtitle">研究热门方向（按标签和技术栈）</div>
          </template>
          <el-empty v-if="!hotTopics.length" description="暂无标签数据" />
          <el-scrollbar v-else class="an-scroll">
            <div class="topics-wrap">
              <span v-for="t in hotTopics" :key="t.name" class="tag">{{ t.name }} · {{ t.count }}</span>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="app-card an-card" shadow="never">
          <template #header>
            <div class="page-subtitle">竞赛参与趋势（最近 6 个月）</div>
          </template>
          <div v-if="!activity.competition_trend.length" style="font-size:12px; color:var(--app-muted);">
            暂无竞赛合作数据。
          </div>
          <div v-else style="border:1px solid rgba(148,163,184,0.25); border-radius:12px; padding:12px; background:linear-gradient(180deg, rgba(249,115,22,0.08), rgba(255,255,255,0));">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
              <div style="display:flex; gap:10px; align-items:center; font-size:12px; color:var(--app-muted);">
                <span style="display:inline-flex; align-items:center; gap:6px;">
                  <span style="width:10px; height:10px; border-radius:999px; background:#f97316;"></span>
                  确认合作数
                </span>
              </div>
              <div style="font-size:11px; color:var(--app-muted);">{{ activity.competition_trend[0].month }} - {{ activity.competition_trend[activity.competition_trend.length - 1].month }}</div>
            </div>
            <svg :viewBox="`0 0 ${trendChart.w} ${trendChart.h}`" :width="'100%'" :height="140" style="display:block;">
              <defs>
                <linearGradient id="gradComp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#f97316" stop-opacity="0.28" />
                  <stop offset="100%" stop-color="#f97316" stop-opacity="0" />
                </linearGradient>
              </defs>

              <g opacity="0.35">
                <line
                  v-for="x in trendChart.gridX"
                  :key="x"
                  :x1="x"
                  :x2="x"
                  :y1="trendChart.padT"
                  :y2="trendChart.h - trendChart.padB"
                  stroke="#94a3b8"
                  stroke-width="1"
                  stroke-dasharray="3 6"
                />
                <line
                  v-for="y in trendChart.gridY"
                  :key="y"
                  :y1="y"
                  :y2="y"
                  :x1="trendChart.padL"
                  :x2="trendChart.w - trendChart.padR"
                  stroke="#94a3b8"
                  stroke-width="1"
                  stroke-dasharray="3 6"
                />
              </g>

              <path :d="compArea" fill="url(#gradComp)" />
              <path :d="compPath" fill="none" stroke="#f97316" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
              <g>
                <circle v-for="p in compDots" :key="`c-${p.x}`" :cx="p.x" :cy="p.y" r="2.8" fill="#f97316" />
              </g>
            </svg>
          </div>
          <div style="margin-top:8px; font-size:11px; color:var(--app-muted);">
            {{ competitionConclusion }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";


const activity = ref<any>({
  posts_daily: [],
  messages_daily: [],
  posts_monthly: [],
  messages_monthly: [],
  competition_trend: []
});
const hotTopics = ref<any[]>([]);


async function load() {
  const analyticsResp = await axios.get("/api/admin/analytics");
  activity.value = analyticsResp.data;
  hotTopics.value = analyticsResp.data.hot_topics || [];
}


const activityChart = computed(() => {
  return {
    w: 640,
    h: 160,
    padL: 18,
    padR: 18,
    padT: 16,
    padB: 18,
    gridX: [1, 2, 3, 4].map(i => 18 + ((640 - 18 - 18) * i) / 5),
    gridY: [1, 2, 3].map(i => 16 + ((160 - 16 - 18) * i) / 4)
  };
});


const trendChart = computed(() => {
  return {
    w: 640,
    h: 160,
    padL: 18,
    padR: 18,
    padT: 16,
    padB: 18,
    gridX: [1, 2, 3, 4].map(i => 18 + ((640 - 18 - 18) * i) / 5),
    gridY: [1, 2, 3].map(i => 16 + ((160 - 16 - 18) * i) / 4)
  };
});


function buildLineSeries(xs: any[], ys: any[], chart: any, maxY: number) {
  const points = xs.map((x, idx) => {
    const v = ys[idx] ?? 0;
    const ratio = maxY > 0 ? v / maxY : 0;
    const cx = chart.padL + ((chart.w - chart.padL - chart.padR) * idx) / Math.max(xs.length - 1, 1);
    const cy = chart.padT + (chart.h - chart.padT - chart.padB) * (1 - ratio);
    return { x: cx, y: cy };
  });
  const path = points
    .map((p, idx) => `${idx === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
  const area = [
    points.length
      ? `M${points[0].x.toFixed(1)},${(chart.h - chart.padB).toFixed(1)}`
      : `M${chart.padL},${(chart.h - chart.padB).toFixed(1)}`,
    ...points.map(p => `L${p.x.toFixed(1)},${p.y.toFixed(1)}`),
    points.length
      ? `L${points[points.length - 1].x.toFixed(1)},${(chart.h - chart.padB).toFixed(1)} Z`
      : `L${chart.w - chart.padR},${(chart.h - chart.padB).toFixed(1)} Z`,
  ].join(" ");
  return { path, area, points };
}


const postsPath = computed(() => buildLineSeries(activity.value.posts_daily || [], (activity.value.posts_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.posts_daily || []).map((d: any) => d.count || 0), 1)).path);
const postsArea = computed(() => buildLineSeries(activity.value.posts_daily || [], (activity.value.posts_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.posts_daily || []).map((d: any) => d.count || 0), 1)).area);
const postsDots = computed(() => buildLineSeries(activity.value.posts_daily || [], (activity.value.posts_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.posts_daily || []).map((d: any) => d.count || 0), 1)).points);

const msgsPath = computed(() => buildLineSeries(activity.value.messages_daily || [], (activity.value.messages_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.messages_daily || []).map((d: any) => d.count || 0), 1)).path);
const msgsArea = computed(() => buildLineSeries(activity.value.messages_daily || [], (activity.value.messages_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.messages_daily || []).map((d: any) => d.count || 0), 1)).area);
const msgsDots = computed(() => buildLineSeries(activity.value.messages_daily || [], (activity.value.messages_daily || []).map((d: any) => d.count || 0), activityChart.value, Math.max(...(activity.value.messages_daily || []).map((d: any) => d.count || 0), 1)).points);


const compPath = computed(() => buildLineSeries(activity.value.competition_trend || [], (activity.value.competition_trend || []).map((d: any) => d.count || 0), trendChart.value, Math.max(...(activity.value.competition_trend || []).map((d: any) => d.count || 0), 1)).path);
const compArea = computed(() => buildLineSeries(activity.value.competition_trend || [], (activity.value.competition_trend || []).map((d: any) => d.count || 0), trendChart.value, Math.max(...(activity.value.competition_trend || []).map((d: any) => d.count || 0), 1)).area);
const compDots = computed(() => buildLineSeries(activity.value.competition_trend || [], (activity.value.competition_trend || []).map((d: any) => d.count || 0), trendChart.value, Math.max(...(activity.value.competition_trend || []).map((d: any) => d.count || 0), 1)).points);


const activityConclusion = computed(() => {
  const totalPosts = (activity.value.posts_daily || []).reduce((s: number, d: any) => s + (d.count || 0), 0);
  const totalMsgs = (activity.value.messages_daily || []).reduce((s: number, d: any) => s + (d.count || 0), 0);
  if (!totalPosts && !totalMsgs) return "最近暂无明显活跃度波动。";
  if (totalMsgs > totalPosts * 2) return "沟通量明显高于发布量，说明平台更偏向即时交流。";
  if (totalPosts > totalMsgs * 2) return "发布量明显高于沟通量，可鼓励同学在交流区多互动。";
  return "发布与沟通整体较为均衡。";
});


const competitionConclusion = computed(() => {
  const total = (activity.value.competition_trend || []).reduce((s: number, d: any) => s + (d.count || 0), 0);
  if (!total) return "最近暂未形成规模化的竞赛合作记录。";
  return `最近 ${activity.value.competition_trend.length} 个月共确认 ${total} 个竞赛合作项目。`;
});


onMounted(() => {
  load();
});
</script>

<style scoped>
.an-row {
  align-items: stretch;
}

.an-card {
  height: 320px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.an-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.an-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.topics-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  padding-right: 6px;
}
</style>
