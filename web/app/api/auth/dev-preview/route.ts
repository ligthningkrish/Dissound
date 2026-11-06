import { NextResponse } from "next/server";
import { getLastSimulatedOtp } from "@/lib/email";

export async function GET() {
  const latest = getLastSimulatedOtp();
  return NextResponse.json({
    available: !!latest,
    data: latest || null,
  });
}
