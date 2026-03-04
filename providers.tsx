"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useAuthStore } from "@/store/authStore";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

export function Providers({ children }: { children: React.ReactNode }) {
  const init = useAuthStore((s) => s.init);
  const initialized = useRef(false);

  useEffect(() => {
    if (!initialized.current) {
      init();
      initialized.current = true;
    }
  }, [init]);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
