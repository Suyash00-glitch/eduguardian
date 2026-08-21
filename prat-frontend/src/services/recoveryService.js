import { demoRecoveryPlan } from "./demoData";

export const recoveryService = {
  async getPlan() {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return demoRecoveryPlan;
  },

  async completeTask(taskId) {
    await new Promise((resolve) => setTimeout(resolve, 300));

    return {
      success: true,
      taskId,
    };
  },
};
