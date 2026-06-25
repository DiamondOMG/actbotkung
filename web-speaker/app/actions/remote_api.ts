"use server";

import axios from "axios";

/**
 * Trigger a remote API call for a specific screen/sequence.
 * 
 * @param sequence_id - The ID of the screen or sequence (e.g., "0200068F2535")
 * @param name - The name parameter for the trigger (e.g., "monitor_tops_bangkhae_map")
 */
export async function remote_api(sequence_id: string, name: string) {
  const url = `https://screens.omg.group/api/screen-trigger/${sequence_id}`;
  
  try {
    const response = await axios.get(url, {
      params: {
        name: name
      }
    });
    return response.data;
  } catch (error: any) {
    console.error(
      "Error in remote_api:", 
      error?.response?.data || error.message
    );
    throw error;
  }
}
