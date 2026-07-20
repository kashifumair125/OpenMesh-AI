"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function WorkflowsPage() {
  const router = useRouter();
  useEffect(() => {
    router.push("/");
  }, [router]);
  return null;
}
