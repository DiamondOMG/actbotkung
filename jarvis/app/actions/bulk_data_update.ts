"use server";

import { axios_targetr } from "../../lib/axios";

/**
 * Update screens with a specific sequence ID.
 * 
 * @param screens - Array of screen IDs
 * @param sequenceId - The sequence ID to assign
 */
export async function bulk_data_update_screen_with_sequence(screens: string[], sequenceId: string) {
  const body = {
    type: "screen",
    ids: screens,
    data: {
      sequenceId: sequenceId,
    },
  };

  try {
    const response = await axios_targetr.post("/api/bulk-data-update", body);
    return response.data;
  } catch (error: any) {
    console.error(
      "Error in bulk_data_update_screen_with_sequence:", 
      error?.response?.data || error.message
    );
    throw error;
  }
}
