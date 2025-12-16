<template>
  <div class="interactions">
    <el-space :size="4">
      <el-button
        size="small"
        text
        :type="state.liked ? 'primary' : 'default'"
        @click="toggleLike"
      >
        点赞 {{ state.likes }}
      </el-button>
      <el-button
        size="small"
        text
        :type="state.favorited ? 'warning' : 'default'"
        @click="toggleFavorite"
      >
        收藏 {{ state.favorites }}
      </el-button>
      <el-button v-if="enableComments" size="small" text @click="openComments">
        评论 {{ state.comments }}
      </el-button>
    </el-space>

    <el-drawer v-if="enableComments" v-model="commentsVisible" title="评论" size="520px" direction="rtl">
      <div class="drawer-wrap">
        <el-empty v-if="!commentTree.length" description="暂无评论" />
        <el-scrollbar v-else class="comment-scroll">
          <div style="display:flex; flex-direction:column; gap:10px; padding-right:6px;">
            <div v-for="c in commentTree" :key="c.id">
              <div class="c-item">
                <div class="c-avatar">{{ avatarText(c.author?.display_name) }}</div>
                <div class="c-main">
                  <div class="c-head">
                    <span class="c-name">{{ c.author?.display_name || "用户" }}</span>
                    <span class="c-time">{{ formatFullTime(c.created_at) }}</span>
                  </div>
                  <div class="c-content">{{ c.content }}</div>
                  <div class="c-actions">
                    <el-button size="small" text @click="replyTo(c)">回复</el-button>
                  </div>
                </div>
              </div>

              <div v-if="c.children && c.children.length" style="margin-left:38px; margin-top:6px; display:flex; flex-direction:column; gap:8px;">
                <div v-for="r in c.children" :key="r.id" class="c-item reply">
                  <div class="c-avatar small">{{ avatarText(r.author?.display_name) }}</div>
                  <div class="c-main">
                    <div class="c-head">
                      <span class="c-name">{{ r.author?.display_name || "用户" }}</span>
                      <span class="c-time">{{ formatFullTime(r.created_at) }}</span>
                    </div>
                    <div class="c-content">
                      <span v-if="r.reply_to" style="color:var(--app-muted);">回复 @{{ r.reply_to }}：</span>
                      {{ r.content }}
                    </div>
                    <div class="c-actions">
                      <el-button size="small" text @click="replyTo(r)">回复</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>

        <div v-if="comments.total > comments.pageSize" style="text-align:right; flex: 0 0 auto;">
          <el-pagination
            background
            layout="prev, pager, next"
            :current-page="comments.page"
            :page-size="comments.pageSize"
            :total="comments.total"
            @current-change="handleCommentsPageChange"
          />
        </div>

        <div style="border-top:1px solid rgba(148,163,184,0.25); padding-top:10px; flex: 0 0 auto;">
          <div v-if="replyTarget" style="font-size:12px; color:var(--app-muted); display:flex; align-items:center; justify-content:space-between;">
            <span>回复 @{{ replyTarget.author?.display_name || "用户" }}</span>
            <el-button size="small" text @click="cancelReply">取消回复</el-button>
          </div>
          <el-input
            v-model="commentInput"
            type="textarea"
            :rows="3"
            maxlength="300"
            show-word-limit
            :placeholder="replyTarget ? '写下回复内容' : '写下你的看法'"
          />
          <div style="margin-top:8px; display:flex; justify-content:flex-end; gap:8px;">
            <el-button size="small" @click="commentsVisible = false">关闭</el-button>
            <el-button type="primary" size="small" @click="submitComment">发布评论</el-button>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import axios from "axios";


const props = withDefaults(defineProps<{
  targetType: string;
  targetId: number;
  enableComments?: boolean;
}>(), {
  enableComments: true
});

const emit = defineEmits(["changed"]);


const state = reactive({
  likes: 0,
  favorites: 0,
  comments: 0,
  liked: false,
  favorited: false
});

const commentsVisible = ref(false);
const commentInput = ref("");
const comments = reactive<{ items: any[]; total: number; page: number; pageSize: number }>(
  {
    items: [],
    total: 0,
    page: 1,
    pageSize: 10
  }
);
const replyTarget = ref<any | null>(null);


const enableComments = computed(() => props.enableComments !== false);


async function loadSummary() {
  if (!props.targetId) return;
  const resp = await axios.get("/api/interactions/summary", {
    params: { target_type: props.targetType, target_id: props.targetId }
  });
  state.likes = resp.data.likes;
  state.favorites = resp.data.favorites;
  state.comments = resp.data.comments;
  state.liked = resp.data.liked;
  state.favorited = resp.data.favorited;
  emit("changed");
}


async function toggleLike() {
  if (!props.targetId) return;
  await axios.post("/api/reactions/toggle", {
    target_type: props.targetType,
    target_id: props.targetId,
    reaction_type: "like"
  });
  await loadSummary();
}


async function toggleFavorite() {
  if (!props.targetId) return;
  await axios.post("/api/reactions/toggle", {
    target_type: props.targetType,
    target_id: props.targetId,
    reaction_type: "favorite"
  });
  await loadSummary();
}


async function loadComments() {
  if (!props.targetId) return;
  const resp = await axios.get("/api/comments", {
    params: {
      target_type: props.targetType,
      target_id: props.targetId,
      page: comments.page,
      page_size: comments.pageSize
    }
  });
  comments.items = resp.data.items || [];
  comments.total = resp.data.total || 0;
}


const commentTree = computed(() => {
  const map = new Map<number, any>();
  const roots: any[] = [];
  const rootById = new Map<number, any>();

  (comments.items || []).forEach((c: any) => {
    map.set(c.id, { ...c, children: [] });
  });

  function findRoot(id: number): any {
    let cur = map.get(id);
    if (!cur) return null;
    const visited = new Set<number>();
    while (cur && cur.parent_comment_id && map.has(cur.parent_comment_id)) {
      if (visited.has(cur.id)) break;
      visited.add(cur.id);
      cur = map.get(cur.parent_comment_id);
    }
    return cur;
  }

  (comments.items || []).forEach((c: any) => {
    const node = map.get(c.id);
    if (!node) return;
    if (!c.parent_comment_id || !map.has(c.parent_comment_id)) {
      roots.push(node);
      rootById.set(node.id, node);
      return;
    }
    const root = findRoot(c.id);
    if (!root) {
      roots.push(node);
      rootById.set(node.id, node);
      return;
    }
    const rootNode = rootById.get(root.id) || root;
    rootById.set(root.id, rootNode);
    const parent = map.get(c.parent_comment_id);
    node.reply_to = parent?.author?.display_name || null;
    rootNode.children.push(node);
  });

  roots.forEach(r => {
    r.children.sort((a: any, b: any) => (a.created_at || "").localeCompare(b.created_at || ""));
  });
  return roots;
});


function openComments() {
  commentsVisible.value = true;
  comments.page = 1;
  replyTarget.value = null;
  loadComments();
}


async function submitComment() {
  const content = commentInput.value.trim();
  if (!content || !props.targetId) return;
  await axios.post("/api/comments", {
    target_type: props.targetType,
    target_id: props.targetId,
    content,
    parent_comment_id: replyTarget.value ? replyTarget.value.id : undefined
  });
  commentInput.value = "";
  replyTarget.value = null;
  comments.page = 1;
  await loadComments();
  await loadSummary();
}


function handleCommentsPageChange(p: number) {
  comments.page = p;
  loadComments();
}


function replyTo(c: any) {
  if (!c) return;
  replyTarget.value = c;
}


function cancelReply() {
  replyTarget.value = null;
}


function avatarText(name?: string) {
  const t = (name || "").trim();
  return t ? t.slice(0, 1) : "U";
}


function formatFullTime(iso?: string) {
  if (!iso) return "";
  return iso.slice(0, 16).replace("T", " ");
}


watch(
  () => props.targetId,
  () => {
    loadSummary();
  }
);


onMounted(() => {
  loadSummary();
});
</script>

<style scoped>
.interactions {
  display: inline-flex;
}

:deep(.el-drawer__body) {
  height: 100%;
  overflow: hidden;
}

.drawer-wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-scroll {
  flex: 1 1 auto;
  min-height: 0;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 12px;
  padding: 10px;
  background: rgba(148, 163, 184, 0.06);
}

.c-item {
  display: flex;
  gap: 10px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: #fff;
}

.c-item.reply {
  background: rgba(148, 163, 184, 0.08);
}

.c-avatar {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #0f172a;
  flex: 0 0 auto;
}

.c-avatar.small {
  width: 26px;
  height: 26px;
  border-radius: 9px;
}

.c-main {
  flex: 1;
  min-width: 0;
}

.c-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.c-name {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
}

.c-time {
  font-size: 11px;
  color: var(--app-muted);
}

.c-content {
  font-size: 12px;
  color: #0f172a;
  margin-top: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.c-actions {
  margin-top: 2px;
}
</style>
