import { demoCoachReplies } from "./demoData";

export const coachService = {
  async sendMessage(message) {
    await new Promise((resolve) => setTimeout(resolve, 800));

    const key = message.toLowerCase();

    if (key.includes("attendance")) {
      return demoCoachReplies.attendance;
    }

    if (key.includes("study") || key.includes("plan")) {
      return demoCoachReplies.study;
    }

    if (key.includes("assignment")) {
      return demoCoachReplies.assignment;
    }

    return demoCoachReplies.default;
  },
};
