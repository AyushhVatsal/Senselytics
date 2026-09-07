import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteDataset,
  listDatasets,
  renameDataset,
  uploadDataset,
} from "@/services/datasetService";

export function useDatasets() {
  return useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
    refetchInterval: (query) => {
      // Poll while any dataset is still importing so status flips to
      // "ready" without a manual refresh.
      const data = query.state.data;
      const hasPending = data?.some(
        (d) => d.status !== "ready" && d.status !== "failed"
      );
      return hasPending ? 3000 : false;
    },
  });
}

export function useUploadDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, file }: { name: string; file: File }) =>
      uploadDataset(name, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useRenameDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      renameDataset(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteDataset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
