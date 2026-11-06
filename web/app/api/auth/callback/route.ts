import { NextRequest, NextResponse } from "next/server";
import { storePendingOtp, DiscordUser, DiscordGuild } from "@/lib/auth";
import { sendOtpEmail } from "@/lib/email";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const error = searchParams.get("error");

  if (error || !code) {
    return NextResponse.redirect(new URL(`/?error=${encodeURIComponent(error || "Access Denied")}`, request.url));
  }

  const clientId = process.env.DISCORD_CLIENT_ID;
  const clientSecret = process.env.DISCORD_CLIENT_SECRET;
  const redirectUri = process.env.DISCORD_REDIRECT_URI || "http://localhost:3000/api/auth/callback";

  try {
    // 1. Exchange code for access token with Discord API
    const tokenResponse = await fetch("https://discord.com/api/v10/oauth2/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: clientId || "",
        client_secret: clientSecret || "",
        grant_type: "authorization_code",
        code,
        redirect_uri: redirectUri,
      }),
    });

    if (!tokenResponse.ok) {
      const errText = await tokenResponse.text();
      console.error("Discord token exchange failed:", errText);
      return NextResponse.redirect(new URL("/?error=token_exchange_failed", request.url));
    }

    const tokenData = await tokenResponse.json();
    const accessToken = tokenData.access_token;

    // 2. Fetch User Profile (id, username, email)
    const userRes = await fetch("https://discord.com/api/v10/users/@me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!userRes.ok) {
      return NextResponse.redirect(new URL("/?error=user_fetch_failed", request.url));
    }
    const userData: DiscordUser = await userRes.json();

    // 3. Fetch User Guilds
    const guildsRes = await fetch("https://discord.com/api/v10/users/@me/guilds", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const guilds: DiscordGuild[] = guildsRes.ok ? await guildsRes.json() : [];

    if (!userData.email) {
      return NextResponse.redirect(
        new URL("/?error=no_email_associated_with_discord", request.url)
      );
    }

    // 4. Generate & Store 6-Digit OTP and Dispatch Verification Email
    const { otp } = storePendingOtp(userData, guilds);
    await sendOtpEmail({
      toEmail: userData.email,
      username: userData.username,
      otpCode: otp,
    });

    // 5. Redirect to OTP verification page
    const verifyUrl = new URL(
      `/auth/verify-otp?userId=${userData.id}&email=${encodeURIComponent(userData.email)}`,
      request.url
    );
    const response = NextResponse.redirect(verifyUrl);

    response.cookies.set("pending_userId", userData.id, {
      httpOnly: true,
      maxAge: 600, // 10 minutes
      path: "/",
      sameSite: "lax",
    });

    return response;
  } catch (err: any) {
    console.error("OAuth callback exception:", err);
    return NextResponse.redirect(new URL(`/?error=${encodeURIComponent(err.message)}`, request.url));
  }
}
