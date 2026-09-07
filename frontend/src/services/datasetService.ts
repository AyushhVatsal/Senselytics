import { apiClient } from "@/lib/apiClient";
import type { DatasetListResponse, DatasetResponse } from "@/types/api";

export async function listDatasets(): Promise<DatasetListResponse[]> {
  const { data } = await apiClient.get<DatasetListResponse[]>("/datasets");
  return data;
}

export async function getDataset(id: number): Promise<DatasetResponse> {
  const { data } = await apiClient.get<DatasetResponse>(`/datasets/${id}`);
  return data;
}

export async function uploadDataset(
  name: string,
  file: File
): Promise<DatasetResponse> {
  const form = new FormData();
  form.set("name", name);
  form.set("file", file);

  const { data } = await apiClient.post<DatasetResponse>(
    "/datasets/upload",
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120_000, // uploads/imports can take longer than the default
    }
  );
  return data;
}

export async function renameDataset(
  id: number,
  name: string
): Promise<DatasetResponse> {
  const { data } = await apiClient.patch<DatasetResponse>(`/datasets/${id}`, {
    name,
  });
  return data;
}

export async function deleteDataset(id: number): Promise<void> {
  await apiClient.delete(`/datasets/${id}`);
}
