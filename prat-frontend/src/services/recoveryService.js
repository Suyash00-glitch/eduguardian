import { studentService } from "./studentService";

export const recoveryService = {
  async getPlan() {
    return studentService.getRecoveryPlan();
  },

  async completeTask(taskId) {
    return studentService.toggleRecoveryTask(taskId);
  },

  async syncAiStudyPlan(aiPlanData) {
    return studentService.syncAiStudyPlan(aiPlanData);
  },

  async generateAiPlan(prompt) {
    return studentService.generateAiRecoveryPlan(prompt);
  }
};

