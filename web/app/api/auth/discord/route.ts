import { NextRequest, NextResponse } from "next/server";
import { storePendingOtp } from "@/lib/auth";
import { sendOtpEmail } from "@/lib/email";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const isDemo = searchParams.get("demo") === "true";

  const clientId = process.env.DISCORD_CLIENT_ID;
  const redirectUri = process.env.DISCORD_REDIRECT_URI || "http://localhost:3000/api/auth/callback";

  // If developer clicks "Demo Login" or if Client ID isn't configured with real Discord credentials
  if (isDemo || !clientId || clientId === "mock_discord_client_id" || clientId === "your_discord_client_id") {
    // Generate a realistic demo Discord user profile
    const demoUser = {
      id: "987654321098765432",
      username: "GamerKris",
      global_name: "Kris Gaming",
      avatar: "https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80",
      email: "kris.developer@example.com",
      verified: true,
    };

    const demoGuilds = [
      {
        id: "111222333444",
        name: "Meme Legends Discord",
        icon: null,
        owner: true,
        permissions: "8", // Administrator
        features: ["SOUNDBOARD", "COMMUNITY"],
      },
      {
        id: "555666777888",
        name: "Chill Voice & Gaming",
        icon: null,
        owner: false,
        permissions: "1099511627776", // CREATE_GUILD_EXPRESSIONS
        features: ["SOUNDBOARD"],
      },
    ];

    // Store pending OTP and send email
    const { otp } = storePendingOtp(demoUser, demoGuilds);
    await sendOtpEmail({
      toEmail: demoUser.email,
      username: demoUser.username,
      otpCode: otp,
    });

    const response = NextResponse.redirect(
      new URL(`/auth/verify-otp?userId=${demoUser.id}&email=${encodeURIComponent(demoUser.email)}&demo=true`, request.url)
    );

    // Set temporary pending auth cookie (expires in 10 minutes)
    response.cookies.set("pending_userId", demoUser.id, {
      httpOnly: true,
      maxAge: 600,
      path: "/",
      sameSite: "lax",
    });

    return response;
  }

  // Real Discord OAuth2 Authorize URL
  const scope = encodeURIComponent("identify email guilds");
  const encodedRedirect = encodeURIComponent(redirectUri);
  const state = Math.random().toString(36).substring(7);

  const discordAuthUrl = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&redirect_uri=${encodedRedirect}&response_type=code&scope=${scope}&state=${state}`;

  const response = NextResponse.redirect(discordAuthUrl);
  response.cookies.set("oauth_state", state, { httpOnly: true, maxAge: 300, path: "/" });
  return response;
}
