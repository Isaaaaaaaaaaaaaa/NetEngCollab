<template>
  <div class="role-tag-selector">
    <div class="selector-label" v-if="label">{{ label }}</div>
    
    <!-- 已选标签展示 -->
    <div class="selected-tags" v-if="modelValue.length > 0">
      <el-tag
        v-for="tag in modelValue"
        :key="tag"
        closable
        :type="getTagType(tag)"
        @close="removeTag(tag)"
        class="selected-tag"
      >
        {{ tag }}
      </el-tag>
    </div>
    
    <!-- 标签选择器 -->
    <el-popover
      placement="bottom-start"
      :width="360"
      trigger="click"
      v-model:visible="popoverVisible"
    >
      <template #reference>
        <el-button size="small" type="primary" plain>
          <el-icon style="margin-right: 4px;"><Plus /></el-icon>
          {{ addButtonText }}
        </el-button>
      </template>
      
      <div class="tag-popover">
        <!-- 搜索/添加自定义标签 -->
        <div class="custom-input">
          <el-input
            v-model="customTag"
            size="small"
            placeholder="搜索或输入自定义标签"
            clearable
            @keyup.enter="addCustomTag"
          >
            <template #append>
              <el-button @click="addCustomTag" :disabled="!customTag.trim()">添加</el-button>
            </template>
          </el-input>
        </div>
        
        <!-- 预设标签列表 -->
        <div class="preset-tags">
          <div class="tag-group-title">预设角色</div>
          <div class="tag-list">
            <span
              v-for="tag in filteredPresetTags"
              :key="tag"
              class="selectable-tag"
              :class="{ 'is-selected': isSelected(tag) }"
              @click="toggleTag(tag)"
            >
              <span class="tag-text">{{ tag }}</span>
              <el-icon v-if="isSelected(tag)" class="check-icon"><Check /></el-icon>
            </span>
          </div>
        </div>
        
        <!-- 自定义标签列表 -->
        <div class="custom-tags" v-if="customTags.length > 0">
          <div class="tag-group-title">自定义角色</div>
          <div class="tag-list">
            <span
              v-for="tag in filteredCustomTags"
              :key="tag"
              class="selectable-tag custom"
              :class="{ 'is-selected': isSelected(tag) }"
              @click="toggleTag(tag)"
            >
              <span class="tag-text">{{ tag }}</span>
              <el-icon v-if="isSelected(tag)" class="check-icon"><Check /></el-icon>
            </span>
          </div>
        </div>
        
        <!-- 建议标签（来自项目要求） -->
        <div class="suggested-tags" v-if="suggestedTags.length > 0">
          <div class="tag-group-title">项目招募角色（建议）</div>
          <div class="tag-list">
            <span
              v-for="tag in suggestedTags"
              :key="'suggested-' + tag"
              class="selectable-tag suggested"
              :class="{ 'is-selected': isSelected(tag) }"
              @click="toggleTag(tag)"
            >
              <span class="tag-text">{{ tag }}</span>
              <el-icon v-if="isSelected(tag)" class="check-icon"><Check /></el-icon>
            </span>
          </div>
        </div>
      </div>
    </el-popover>
    
    <!-- 提示文字 -->
    <div class="selector-hint" v-if="hint">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { Plus, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: string[]
  label?: string
  hint?: string
  addButtonText?: string
  suggestedTags?: string[]  // 项目招募的角色标签，作为建议
  maxTags?: number
}

const props = withDefaults(defineProps<Props>(), {
  label: '',
  hint: '',
  addButtonText: '添加角色标签',
  suggestedTags: () => [],
  maxTags: 5
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const popoverVisible = ref(false)
const customTag = ref('')
const presetTags = ref<string[]>([])
const customTags = ref<string[]>([])

// 加载标签列表
const loadTags = async () => {
  try {
    const response = await axios.get('/api/role-tags')
    presetTags.value = response.data.preset_tags || []
    customTags.value = response.data.custom_tags || []
  } catch (err) {
    console.error('加载角色标签失败:', err)
  }
}

// 过滤后的预设标签
const filteredPresetTags = computed(() => {
  if (!customTag.value.trim()) return presetTags.value
  const keyword = customTag.value.toLowerCase()
  return presetTags.value.filter(tag => tag.toLowerCase().includes(keyword))
})

// 过滤后的自定义标签
const filteredCustomTags = computed(() => {
  if (!customTag.value.trim()) return customTags.value
  const keyword = customTag.value.toLowerCase()
  return customTags.value.filter(tag => tag.toLowerCase().includes(keyword))
})

// 检查标签是否已选中
const isSelected = (tag: string) => {
  return props.modelValue.includes(tag)
}

// 获取标签类型
const getTagType = (tag: string) => {
  if (props.suggestedTags.includes(tag)) return 'primary'
  if (presetTags.value.includes(tag)) return 'success'
  return 'warning'
}

// 切换标签选中状态
const toggleTag = (tag: string) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(tag)
  
  if (index > -1) {
    newValue.splice(index, 1)
  } else {
    if (newValue.length >= props.maxTags) {
      ElMessage.warning(`最多只能选择 ${props.maxTags} 个角色标签`)
      return
    }
    newValue.push(tag)
  }
  
  emit('update:modelValue', newValue)
}

// 移除标签
const removeTag = (tag: string) => {
  const newValue = props.modelValue.filter(t => t !== tag)
  emit('update:modelValue', newValue)
}

// 添加自定义标签
const addCustomTag = async () => {
  const tag = customTag.value.trim()
  if (!tag) return
  
  if (tag.length > 32) {
    ElMessage.error('角色标签不能超过32个字符')
    return
  }
  
  if (props.modelValue.length >= props.maxTags) {
    ElMessage.warning(`最多只能选择 ${props.maxTags} 个角色标签`)
    return
  }
  
  // 如果标签不在预设和自定义列表中，添加到后端
  if (!presetTags.value.includes(tag) && !customTags.value.includes(tag)) {
    try {
      await axios.post('/api/role-tags', { tag_name: tag })
      customTags.value.push(tag)
    } catch (err) {
      console.error('添加自定义标签失败:', err)
    }
  }
  
  // 添加到已选列表
  if (!props.modelValue.includes(tag)) {
    emit('update:modelValue', [...props.modelValue, tag])
  }
  
  customTag.value = ''
}

onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.role-tag-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 28px;
}

.selected-tag {
  margin: 0 !important;
}

.selector-hint {
  font-size: 12px;
  color: #909399;
}

.tag-popover {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.custom-input {
  margin-bottom: 4px;
}

.tag-group-title {
  font-size: 12px;
  font-weight: 500;
  color: #909399;
  margin-bottom: 6px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.selectable-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: #f4f4f5;
  color: #909399;
  border: 1px solid #e9e9eb;
}

.selectable-tag:hover {
  background: #ecf5ff;
  color: #409eff;
  border-color: #b3d8ff;
}

.selectable-tag.is-selected {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}

.selectable-tag.custom {
  background: #fdf6ec;
  color: #e6a23c;
  border-color: #faecd8;
}

.selectable-tag.custom:hover {
  background: #fef0e6;
  border-color: #f5dab1;
}

.selectable-tag.custom.is-selected {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}

.selectable-tag.suggested {
  background: #ecf5ff;
  color: #409eff;
  border-color: #d9ecff;
}

.selectable-tag.suggested:hover {
  background: #d9ecff;
  border-color: #b3d8ff;
}

.selectable-tag.suggested.is-selected {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}

.tag-text {
  line-height: 1;
}

.check-icon {
  margin-left: 4px;
  font-size: 12px;
}

.preset-tags,
.custom-tags,
.suggested-tags {
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.suggested-tags {
  border-bottom: none;
}
</style>
