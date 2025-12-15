<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">平台总体数据</h2>
        <p class="page-subtitle">为专业建设提供数据支撑</p>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">注册用户</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.users }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">包含学生、教师和管理员账号总数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">教师发布项目</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.teacher_posts }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">当前系统中的科研 / 大创 / 竞赛条目</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">资源条目</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.resources }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">用于教学与竞赛的资源文件数量</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">师生合作概览</div>
      </template>
      <el-row :gutter="16">
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">合作总数</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px;">{{ coopSummary.total }}</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">已确认合作</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px; color:#16a34a;">{{ coopSummary.confirmed }}</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">待处理 / 已拒绝</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px;">{{ coopSummary.pending }} / {{ coopSummary.rejected }}</div>
        </el-col>
      </el-row>
    </el-card>

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

    <el-row :gutter="16" style="margin-top:16px;">
      <el-col :xs="24" :lg="12">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">研究热门方向（按标签和技术栈）</div>
          </template>
          <el-empty v-if="!hotTopics.length" description="暂无标签数据" />
          <div v-else style="display:flex; flex-wrap:wrap; gap:6px; font-size:12px;">
            <span
              v-for="t in hotTopics"
              :key="t.name"
              class="tag"
            >
              {{ t.name }} · {{ t.count }}
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="app-card" shadow="never">
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


const stats = ref<any>({ users: 0, teacher_posts: 0, resources: 0 });
const coopSummary = ref<any>({ total: 0, confirmed: 0, rejected: 0, pending: 0 });
const activity = ref<any>({
  posts_daily: [],
  messages_daily: [],
  posts_monthly: [],
  messages_monthly: [],
  competition_trend: []
});
const hotTopics = ref<any[]>([]);


async function load() {
  const [statsResp, coopResp, analyticsResp] = await Promise.all([
    axios.get("/api/admin/stats"),
    axios.get("/api/admin/cooperations"),
    axios.get("/api/admin/analytics")
  ]);
  stats.value = statsResp.data;
  coopSummary.value = coopResp.data.summary || coopSummary.value;
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


function toPoints(counts: number[], chart: any): { x: number; y: number }[] {
  const max = Math.max(...counts, 1);
  const innerW = chart.w - chart.padL - chart.padR;
  const innerH = chart.h - chart.padT - chart.padB;
  const n = counts.length || 1;
  return counts.map((v, i) => {
    const x = chart.padL + (n === 1 ? innerW / 2 : (innerW * i) / (n - 1));
    const y = chart.padT + (1 - v / max) * innerH;
    return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
  });
}


function smoothPath(points: { x: number; y: number }[]): string {
  if (!points.length) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const mx = (p0.x + p1.x) / 2;
    const my = (p0.y + p1.y) / 2;
    d += ` Q ${p0.x} ${p0.y} ${mx} ${my}`;
  }
  const last = points[points.length - 1];
  d += ` T ${last.x} ${last.y}`;
  return d;
}


function areaPath(points: { x: number; y: number }[], chart: any): string {
  if (!points.length) return "";
  const baseY = chart.h - chart.padB;
  const first = points[0];
  const last = points[points.length - 1];
  return `${smoothPath(points)} L ${last.x} ${baseY} L ${first.x} ${baseY} Z`;
}


const postsDots = computed(() => {
  const counts = (activity.value.posts_daily || []).map((d: any) => d.count || 0);
  return toPoints(counts, activityChart.value);
});


const msgsDots = computed(() => {
  const counts = (activity.value.messages_daily || []).map((d: any) => d.count || 0);
  return toPoints(counts, activityChart.value);
});


const postsPath = computed(() => smoothPath(postsDots.value));
const msgsPath = computed(() => smoothPath(msgsDots.value));
const postsArea = computed(() => areaPath(postsDots.value, activityChart.value));
const msgsArea = computed(() => areaPath(msgsDots.value, activityChart.value));


const compDots = computed(() => {
  const counts = (activity.value.competition_trend || []).map((m: any) => m.count || 0);
  return toPoints(counts, trendChart.value);
});
const compPath = computed(() => smoothPath(compDots.value));
const compArea = computed(() => areaPath(compDots.value, trendChart.value));


const activityConclusion = computed(() => {
  const posts = activity.value.posts_daily || [];
  const msgs = activity.value.messages_daily || [];
  if (!posts.length && !msgs.length) return "近 14 天缺少活跃数据，后续可通过发布项目和使用私信提高活跃度。";
  const topPost = [...posts].sort((a: any, b: any) => (b.count || 0) - (a.count || 0))[0];
  const topMsg = [...msgs].sort((a: any, b: any) => (b.count || 0) - (a.count || 0))[0];
  return `项目发布高峰出现在 ${topPost?.date || "-"}，沟通高峰出现在 ${topMsg?.date || "-"}，整体活跃度呈现平稳分布，可在高峰前后集中安排教学与辅导。`;
});


const competitionConclusion = computed(() => {
  const trend = activity.value.competition_trend || [];
  if (!trend.length) return "最近 6 个月暂无竞赛合作记录，可引导老师发布更多竞赛类项目并鼓励学生参与。";
  const maxItem = [...trend].sort((a: any, b: any) => (b.count || 0) - (a.count || 0))[0];
  const last = trend[trend.length - 1];
  if ((last?.count || 0) >= (maxItem?.count || 0)) {
    return `竞赛合作在 ${last.month} 达到高位，呈上升趋势`;
  }
  return `竞赛合作高峰出现在 ${maxItem.month}，最近月份略有回落，可通过组织宣讲和分享会继续提升学生的参赛积极性。`;
});


onMounted(() => {
  load();
});
</script>
