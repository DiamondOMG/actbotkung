"use server";

import { axios_targetr } from "../../lib/axios";

interface PlaybackData {
  data: {
    screenId: string;
  };
  result: {
    item: {
      data: { libraryItemId: string; label: string };
      resources: {
        data: { width: string; blobId: string };
      }[];
    };
  }[];
}

export async function screen_by_id(screen_id: string) {
  const response = await axios_targetr.get(`/rest-api/v1/screens/${screen_id}`);
  return response.data;
}

export async function playback_screen_by_id(screen_id: string) {
  const { data } = await axios_targetr.get<PlaybackData>(
    `/api/simulate-screen/${screen_id}`
  );

  return data.result.map((entry) => {
    const resource = entry.item.resources.find((r) => r.data.width === "200");

    return {
      screenId: data.data.screenId,
      libraryItemId: entry.item.data.libraryItemId,
      label: entry.item.data.label,
      blobId: resource?.data.blobId ?? null,
    };
  });
}

export async function bulk_data_update(
  ids: string[],
  dpop_endpoint: string,
  dpop_type: string
) {
  try {
    const { data } = await axios_targetr.post(
      "https://stacks.targetr.net/api/bulk-data-update",
      {
        type: "screen",
        ids: ids,
        data: {
          dpopEndpoint: dpop_endpoint,
          dpopType: dpop_type,
        },
      }
    );
    console.log("Bulk update success:", data);
    return data;
  } catch (error: any) {
    console.error("Bulk update error:", {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
    });
    throw error;
  }
}
