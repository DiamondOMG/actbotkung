"use server";

import { axios_targetr } from "../../lib/axios";


export async function sequence_by_id(sequence_id: string) {
  const response = await axios_targetr.get(`/rest-api/v1/sequences/${sequence_id}`);
  return response.data;
}

