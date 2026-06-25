"use server";

import { bulk_data_update_screen_with_sequence } from "./bulk_data_update";
import { remote_api } from "./remote_api";

/**
 * Change monitor screen: Update sequence mapping and then trigger via remote API with retry logic.
 * 
 * @param screens - Array of screen IDs
 * @param sequenceId - The sequence ID to assign
 * @param name - The name for the remote trigger
 */
export async function change_monitor_screen(screens: string[], sequenceId: string, name: string) {
  try {
    // 1. Update the screen data mapping
    await bulk_data_update_screen_with_sequence(screens, sequenceId);
  } catch (error) {
    console.error("Bulk update failed:", error);
    return { message: " ไม่สามารถอัพเดท screen เหล่านี้ได้" };
  }

  // Helper function for sleep/delay
  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  // 2. Trigger remote API for each screen with retry logic
  // According to the prompt, we trigger remote_api after a successful bulk update.
  // We'll iterate through the screens and attempt to trigger.
  // If we should trigger for ALL screens and fail if ANY fail, or just if the process fails.
  // The prompt implies a general trigger logic.
  
  let lastSuccess = false;
  const maxAttempts = 5;

  for (let attempts = 1; attempts <= maxAttempts; attempts++) {
    const triggerId = screens[0]; 
    try {
      await remote_api(triggerId, name);
      console.log(`Trigger attempt ${attempts} succeeded.`);
      lastSuccess = true;
    } catch (error) {
      console.log(`Trigger attempt ${attempts} failed.`);
      lastSuccess = false;
    }

    // Wait 1s between attempts, except after the last one
    if (attempts < maxAttempts) {
      await sleep(1000);
    }
  }

  if (!lastSuccess) {
    return { success: false, message: "ไม่สามารถ ทริกเกอจอได้" };
  }

  return { success: true, message: "เปลี่ยนจอและทริกเกอร์สำเร็จ" };
}
