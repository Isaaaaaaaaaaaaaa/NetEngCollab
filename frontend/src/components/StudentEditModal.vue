<template>
  <el-dialog
    v-model="dialogVisible"
    title="编辑学生信息"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="学生姓名">
        <el-input :value="studentInfo.name" disabled />
      </el-form-item>

      <el-form-item label="项目角色" prop="student_role">
        <el-select 
          v-model="formData.student_role" 
          placeholder="选择或输入角色" 
          filterable 
          allow-create 
          clearable 
          style="width: 100%;"
        >
          <el-option label="前端开发" value="前端开发" />
          <el-option label="后端开发" value="后端开发" />
          <el-option label="算法研究" value="算法研究" />
          <el-option label="数据分析" value="数据分析" />
          <el-option label="测试" value="测试" />
          <el-option label="文档撰写" value="文档撰写" />
          <el-option label="UI设计" value="UI设计" />
          <el-option label="项目管理" value="项目管理" />
        </el-select>
        <template #extra>
          <span style="font-size: 12px; color: #909399;">为学生在项目中分配具体角色</span>
        </template>
      </el-form-item>

      <el-form-item label="自定义状态" prop="custom_status">
        <el-select 
          v-model="formData.custom_status" 
          placeholder="选择或输入状态" 
          filterable 
          allow-create 
          clearable 
          style="width: 100%;"
        >
          <el-option label="进展顺利" value="进展顺利" />
          <el-option label="需要帮助" value="需要帮助" />
          <el-option label="已完成阶段任务" value="已完成阶段任务" />
          <el-option label="待分配任务" value="待分配任务" />
          <el-option label="学习中" value="学习中" />
          <el-option label="暂时搁置" value="暂时搁置" />
        </el-select>
        <template #extra>
          <span style="font-size: 12px; color: #909399;">标记学生当前的工作状态</span>
        </template>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import axios from 'axios'

interface Props {
  visible: boolean
  cooperationRequestId: number | null
  studentInfo: {
    name: string
    role?: string
    status?: string
  }
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)

const formData = reactive({
  student_role: '',
  custom_status: ''
})

const rules: FormRules = {
  student_role: [
    { max: 64, message: '角色名称不能超过64个字符', trigger: 'blur' }
  ],
  custom_status: [
    { max: 64, message: '状态不能超过64个字符', trigger: 'blur' }
  ]
}

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal) {
    // 初始化表单数据
    formData.student_role = props.studentInfo.role || ''
    formData.custom_status = props.studentInfo.status || ''
  }
})

watch(dialogVisible, (newVal) => {
  if (!newVal) {
    emit('update:visible', false)
    formRef.value?.resetFields()
  }
})

const handleClose = () => {
  dialogVisible.value = false
}

const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  if (!props.cooperationRequestId) {
    ElMessage.error('缺少必要参数')
    return
  }

  saving.value = true

  try {
    await axios.put(
      `/api/cooperation/requests/${props.cooperationRequestId}/student-info`,
      {
        student_role: formData.student_role || null,
        custom_status: formData.custom_status || null
      }
    )

    ElMessage.success('保存成功')
    emit('updated')
    handleClose()
  } catch (error: any) {
    console.error('保存失败:', error)
    const message = error.response?.data?.message || '保存失败，请重试'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
