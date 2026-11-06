import { NextRequest, NextResponse } from "next/server";
import { getPendingOtp, storePendingOtp } from "@/lib/auth";
import { sendOtpEmail } from "@/lib/email";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    let userId = body.userId || request.cookies.get("pending_userId")?.value;

    if (!userId) {
      return NextResponse.json({ success: false, error: "No active session to resend code for." }, { status: 400 });
    }

    const record = getPendingOtp(userId);
    if (!record) {
      return NextResponse.json(
        { success: false, error: "Session expired. Please restart login with Discord." },
        { status: 400 }
      );
    }

    // Generate fresh OTP
    const { otp } = storePendingOtp(record.userData, record.guilds);
    await sendOtpEmail({
      toEmail: record.email,
      username: record.userData.username,
      otpCode: otp,
    });

    return NextResponse.json({
      success: true,
      message: `A fresh 6-digit code has been dispatched to ${record.email}.`,
    });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
