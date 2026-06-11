#include <math.h>
#include <string.h>
double sigmoid(double x) {
    if (x < 0.0) {
        double z = exp(x);
        return z / (1.0 + z);
    }
    return 1.0 / (1.0 + exp(-x));
}
void score(double * input, double * output) {
    double var0;
    if (input[3] < 0.49010453) {
        if (input[0] < 7.528561) {
            if (input[1] < 23.513678) {
                var0 = -0.1689008;
            } else {
                var0 = 0.40444446;
            }
        } else {
            var0 = 0.40219784;
        }
    } else {
        var0 = 0.4777778;
    }
    double var1;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[0] < 6.2990746) {
                var1 = 0.3787412;
            } else {
                var1 = -0.10414324;
            }
        } else {
            var1 = 0.3613395;
        }
    } else {
        var1 = 0.38823482;
    }
    double var2;
    if (input[3] < 0.49971524) {
        if (input[1] < 23.513678) {
            if (input[0] < 7.761515) {
                var2 = -0.10575708;
            } else {
                var2 = 0.3055842;
            }
        } else {
            var2 = 0.34368584;
        }
    } else {
        var2 = 0.33150938;
    }
    double var3;
    if (input[2] < 0.2584414) {
        var3 = 0.35118765;
    } else {
        if (input[0] < 6.2990746) {
            var3 = 0.32097495;
        } else {
            if (input[4] < 203.54034) {
                var3 = 0.35060975;
            } else {
                var3 = -0.049565986;
            }
        }
    }
    double var4;
    if (input[1] < 25.119394) {
        if (input[3] < 0.49971524) {
            if (input[0] < 7.761515) {
                var4 = -0.10264658;
            } else {
                var4 = 0.2709931;
            }
        } else {
            var4 = 0.27949652;
        }
    } else {
        var4 = 0.30795166;
    }
    double var5;
    if (input[4] < 203.5464) {
        var5 = 0.3245073;
    } else {
        if (input[0] < 6.2990746) {
            var5 = 0.28144214;
        } else {
            if (input[1] < 23.513678) {
                var5 = -0.07398264;
            } else {
                var5 = 0.25346926;
            }
        }
    }
    double var6;
    if (input[2] < 0.2584414) {
        var6 = 0.30956122;
    } else {
        if (input[3] < 0.49971524) {
            if (input[0] < 7.761515) {
                var6 = -0.08566933;
            } else {
                var6 = 0.24619041;
            }
        } else {
            var6 = 0.24828392;
        }
    }
    double var7;
    if (input[4] < 203.5464) {
        var7 = 0.2835939;
    } else {
        if (input[0] < 6.2990746) {
            var7 = 0.25290388;
        } else {
            if (input[1] < 25.119394) {
                var7 = -0.0751863;
            } else {
                var7 = 0.2400412;
            }
        }
    }
    double var8;
    if (input[2] < 0.2584414) {
        var8 = 0.2759079;
    } else {
        if (input[3] < 0.49971524) {
            if (input[0] < 7.761515) {
                var8 = -0.08414784;
            } else {
                var8 = 0.22824349;
            }
        } else {
            var8 = 0.22729199;
        }
    }
    double var9;
    if (input[0] < 6.2425766) {
        var9 = 0.2485635;
    } else {
        if (input[4] < 203.5464) {
            var9 = 0.25400248;
        } else {
            if (input[1] < 25.119394) {
                var9 = -0.07491742;
            } else {
                var9 = 0.22713198;
            }
        }
    }
    double var10;
    if (input[2] < 0.2584414) {
        var10 = 0.25044224;
    } else {
        if (input[3] < 0.49971524) {
            if (input[0] < 7.761515) {
                var10 = -0.08022685;
            } else {
                var10 = 0.21306849;
            }
        } else {
            var10 = 0.2106428;
        }
    }
    double var11;
    if (input[0] < 6.2425766) {
        var11 = 0.22946884;
    } else {
        if (input[4] < 203.5464) {
            var11 = 0.23104417;
        } else {
            if (input[1] < 25.119394) {
                var11 = -0.0727149;
            } else {
                var11 = 0.21151985;
            }
        }
    }
    double var12;
    if (input[2] < 0.2584414) {
        var12 = 0.22984177;
    } else {
        if (input[0] < 7.761515) {
            if (input[3] < 0.49971524) {
                var12 = -0.07560408;
            } else {
                var12 = 0.1960874;
            }
        } else {
            var12 = 0.20015396;
        }
    }
    double var13;
    if (input[0] < 6.2425766) {
        var13 = 0.21310145;
    } else {
        if (input[2] < 0.3854102) {
            if (input[2] < 0.2584414) {
                var13 = 0.20636712;
            } else {
                var13 = 0.045617834;
            }
        } else {
            if (input[1] < 25.119394) {
                var13 = -0.094713196;
            } else {
                var13 = 0.18871054;
            }
        }
    }
    double var14;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[4] < 208.92758) {
                var14 = 0.18858363;
            } else {
                var14 = -0.07348345;
            }
        } else {
            var14 = 0.18865743;
        }
    } else {
        var14 = 0.19276306;
    }
    double var15;
    if (input[1] < 9.923827) {
        if (input[0] < 7.581582) {
            if (input[3] < 0.44943362) {
                var15 = -0.10943983;
            } else {
                var15 = 0.10837998;
            }
        } else {
            var15 = 0.12772219;
        }
    } else {
        if (input[3] < 0.253969) {
            var15 = -0.012067766;
        } else {
            var15 = 0.17086972;
        }
    }
    double var16;
    if (input[0] < 6.2425766) {
        var16 = 0.19556238;
    } else {
        if (input[4] < 208.92758) {
            var16 = 0.17335415;
        } else {
            if (input[1] < 23.513678) {
                var16 = -0.074962355;
            } else {
                var16 = 0.15744565;
            }
        }
    }
    double var17;
    if (input[0] < 6.2849293) {
        var17 = 0.17066967;
    } else {
        if (input[0] < 7.761515) {
            if (input[3] < 0.49971524) {
                var17 = -0.072588086;
            } else {
                var17 = 0.16740091;
            }
        } else {
            var17 = 0.17008929;
        }
    }
    double var18;
    if (input[2] < 0.36410525) {
        var18 = 0.14143352;
    } else {
        if (input[4] < 276.47925) {
            if (input[2] < 0.6806068) {
                var18 = 0.014695319;
            } else {
                var18 = 0.11129948;
            }
        } else {
            if (input[0] < 6.595851) {
                var18 = 0.04679222;
            } else {
                var18 = -0.10840482;
            }
        }
    }
    double var19;
    if (input[1] < 23.513678) {
        if (input[2] < 0.3854102) {
            var19 = 0.11287234;
        } else {
            if (input[4] < 229.15123) {
                var19 = 0.10776589;
            } else {
                var19 = -0.08504221;
            }
        }
    } else {
        var19 = 0.15249607;
    }
    double var20;
    if (input[0] < 6.2990746) {
        var20 = 0.14363265;
    } else {
        if (input[0] < 7.6843157) {
            if (input[3] < 0.4430559) {
                var20 = -0.078965254;
            } else {
                var20 = 0.11130116;
            }
        } else {
            var20 = 0.13660945;
        }
    }
    double var21;
    if (input[1] < 9.923827) {
        if (input[4] < 244.94983) {
            var21 = 0.07432045;
        } else {
            if (input[3] < 0.3979436) {
                var21 = -0.08700695;
            } else {
                var21 = 0.048350487;
            }
        }
    } else {
        if (input[2] < 0.83799225) {
            var21 = 0.11718126;
        } else {
            var21 = 0.008505194;
        }
    }
    double var22;
    if (input[0] < 7.6843157) {
        if (input[0] < 6.6163263) {
            if (input[3] < 0.28954768) {
                var22 = 0.016243009;
            } else {
                var22 = 0.12948224;
            }
        } else {
            if (input[4] < 231.67001) {
                var22 = 0.08319159;
            } else {
                var22 = -0.09368583;
            }
        }
    } else {
        var22 = 0.12052861;
    }
    double var23;
    if (input[2] < 0.29095724) {
        var23 = 0.11290863;
    } else {
        if (input[1] < 20.434896) {
            if (input[3] < 0.46319965) {
                var23 = -0.06101272;
            } else {
                var23 = 0.085129894;
            }
        } else {
            var23 = 0.116309404;
        }
    }
    double var24;
    if (input[0] < 7.528561) {
        if (input[0] < 6.595851) {
            var24 = 0.085265055;
        } else {
            if (input[4] < 231.67001) {
                var24 = 0.07127431;
            } else {
                var24 = -0.08286807;
            }
        }
    } else {
        var24 = 0.10202402;
    }
    double var25;
    if (input[1] < 14.244712) {
        if (input[2] < 0.34909746) {
            var25 = 0.07438715;
        } else {
            if (input[4] < 229.15123) {
                var25 = 0.067934476;
            } else {
                var25 = -0.06638168;
            }
        }
    } else {
        var25 = 0.08767455;
    }
    double var26;
    if (input[3] < 0.449517) {
        if (input[0] < 7.477571) {
            if (input[0] < 6.642824) {
                var26 = 0.04813402;
            } else {
                var26 = -0.07676102;
            }
        } else {
            var26 = 0.083064236;
        }
    } else {
        var26 = 0.09070051;
    }
    double var27;
    if (input[1] < 14.244712) {
        if (input[3] < 0.44943362) {
            if (input[4] < 225.6445) {
                var27 = 0.06333315;
            } else {
                var27 = -0.059967056;
            }
        } else {
            var27 = 0.066672206;
        }
    } else {
        var27 = 0.074348204;
    }
    double var28;
    if (input[0] < 7.528561) {
        if (input[0] < 6.595851) {
            var28 = 0.060449895;
        } else {
            if (input[4] < 233.31252) {
                var28 = 0.04446569;
            } else {
                var28 = -0.06167488;
            }
        }
    } else {
        var28 = 0.07839501;
    }
    double var29;
    if (input[2] < 0.3098082) {
        var29 = 0.07619499;
    } else {
        if (input[1] < 16.634787) {
            if (input[4] < 225.65358) {
                var29 = 0.04584997;
            } else {
                var29 = -0.05115077;
            }
        } else {
            var29 = 0.06874459;
        }
    }
    double var30;
    if (input[3] < 0.449517) {
        if (input[0] < 7.477571) {
            if (input[0] < 6.482379) {
                var30 = 0.047896996;
            } else {
                var30 = -0.055597637;
            }
        } else {
            var30 = 0.06593522;
        }
    } else {
        var30 = 0.07442323;
    }
    double var31;
    if (input[3] < 0.31634185) {
        if (input[4] < 320.62726) {
            if (input[3] < 0.25343496) {
                var31 = -0.059141282;
            } else {
                var31 = 0.00089492527;
            }
        } else {
            var31 = 0.03518971;
        }
    } else {
        if (input[1] < 8.193793) {
            var31 = 0.0072686933;
        } else {
            var31 = 0.068068914;
        }
    }
    double var32;
    if (input[3] < 0.449517) {
        if (input[0] < 7.477571) {
            if (input[4] < 231.67001) {
                var32 = 0.050043143;
            } else {
                var32 = -0.050665267;
            }
        } else {
            var32 = 0.055908937;
        }
    } else {
        var32 = 0.06030827;
    }
    double var33;
    if (input[1] < 14.244712) {
        if (input[1] < 5.0043106) {
            if (input[1] < 3.7966366) {
                var33 = -0.026488554;
            } else {
                var33 = 0.080180876;
            }
        } else {
            if (input[1] < 8.193793) {
                var33 = -0.074661046;
            } else {
                var33 = 0.010311196;
            }
        }
    } else {
        var33 = 0.05791373;
    }
    double var34;
    if (input[2] < 0.36410525) {
        var34 = 0.052521106;
    } else {
        if (input[2] < 0.6516473) {
            var34 = -0.056650843;
        } else {
            if (input[4] < 274.24533) {
                var34 = 0.06044793;
            } else {
                var34 = -0.0148505885;
            }
        }
    }
    double var35;
    if (input[0] < 6.496991) {
        var35 = 0.05084482;
    } else {
        if (input[2] < 0.4278389) {
            var35 = 0.044877645;
        } else {
            if (input[4] < 247.97218) {
                var35 = 0.03384139;
            } else {
                var35 = -0.06488977;
            }
        }
    }
    double var36;
    if (input[1] < 14.244712) {
        if (input[4] < 330.03995) {
            if (input[3] < 0.28021672) {
                var36 = -0.05788127;
            } else {
                var36 = 0.0052289427;
            }
        } else {
            var36 = 0.034703225;
        }
    } else {
        var36 = 0.04966512;
    }
    double var37;
    if (input[3] < 0.4430559) {
        if (input[0] < 7.477571) {
            if (input[1] < 8.441515) {
                var37 = -0.06484585;
            } else {
                var37 = 0.016755454;
            }
        } else {
            var37 = 0.047547925;
        }
    } else {
        var37 = 0.046817776;
    }
    double var38;
    if (input[0] < 6.595851) {
        var38 = 0.041554548;
    } else {
        if (input[3] < 0.2597581) {
            var38 = 0.03499944;
        } else {
            if (input[3] < 0.411422) {
                var38 = -0.05294378;
            } else {
                var38 = 0.011316243;
            }
        }
    }
    double var39;
    if (input[3] < 0.28021672) {
        if (input[4] < 320.62726) {
            var39 = -0.046766393;
        } else {
            var39 = 0.024510497;
        }
    } else {
        if (input[0] < 7.259673) {
            if (input[1] < 8.193793) {
                var39 = 0.0021296823;
            } else {
                var39 = 0.06637846;
            }
        } else {
            var39 = -0.021430803;
        }
    }
    double var40;
    if (input[1] < 5.1737514) {
        if (input[1] < 3.9015043) {
            var40 = -0.018030766;
        } else {
            var40 = 0.06827364;
        }
    } else {
        if (input[2] < 0.8586232) {
            if (input[1] < 8.805004) {
                var40 = -0.046203956;
            } else {
                var40 = 0.06012321;
            }
        } else {
            var40 = -0.063046165;
        }
    }
    double var41;
    if (input[0] < 7.4796352) {
        if (input[0] < 7.101732) {
            if (input[1] < 5.0043106) {
                var41 = 0.046042293;
            } else {
                var41 = -0.009932755;
            }
        } else {
            var41 = -0.053683292;
        }
    } else {
        var41 = 0.038826663;
    }
    double var42;
    if (input[3] < 0.4430559) {
        if (input[0] < 7.475212) {
            if (input[2] < 1.0563084) {
                var42 = -0.046614736;
            } else {
                var42 = 0.02513544;
            }
        } else {
            var42 = 0.036375333;
        }
    } else {
        var42 = 0.040915105;
    }
    double var43;
    if (input[0] < 7.252023) {
        if (input[3] < 0.253969) {
            var43 = -0.022822738;
        } else {
            if (input[0] < 6.642824) {
                var43 = 0.06885856;
            } else {
                var43 = 0.005479378;
            }
        }
    } else {
        var43 = -0.025298867;
    }
    double var44;
    if (input[1] < 14.244712) {
        if (input[2] < 0.4278389) {
            var44 = 0.031754248;
        } else {
            if (input[1] < 6.0616684) {
                var44 = 0.017503085;
            } else {
                var44 = -0.06822238;
            }
        }
    } else {
        var44 = 0.033874188;
    }
    double var45;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var45 = -0.064902514;
        } else {
            var45 = 0.042760823;
        }
    } else {
        if (input[4] < 274.24533) {
            var45 = 0.053928733;
        } else {
            var45 = -0.014902491;
        }
    }
    double var46;
    if (input[3] < 0.43504387) {
        if (input[2] < 0.36410525) {
            var46 = 0.03138682;
        } else {
            if (input[4] < 277.82837) {
                var46 = 0.019229755;
            } else {
                var46 = -0.055480618;
            }
        }
    } else {
        var46 = 0.033954777;
    }
    double var47;
    if (input[0] < 6.496991) {
        var47 = 0.034830663;
    } else {
        if (input[0] < 6.882923) {
            var47 = -0.051861733;
        } else {
            if (input[0] < 7.252023) {
                var47 = 0.045049056;
            } else {
                var47 = -0.021493219;
            }
        }
    }
    double var48;
    if (input[0] < 7.4796352) {
        if (input[0] < 7.101732) {
            if (input[0] < 6.882923) {
                var48 = -0.010585742;
            } else {
                var48 = 0.038824923;
            }
        } else {
            var48 = -0.04857299;
        }
    } else {
        var48 = 0.033986896;
    }
    double var49;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var49 = -0.057978466;
        } else {
            var49 = 0.035386406;
        }
    } else {
        if (input[1] < 8.578742) {
            var49 = 0.042351644;
        } else {
            var49 = -0.014657628;
        }
    }
    double var50;
    if (input[1] < 14.244712) {
        if (input[2] < 0.4278389) {
            var50 = 0.025942458;
        } else {
            if (input[1] < 6.0616684) {
                var50 = 0.009560073;
            } else {
                var50 = -0.05845111;
            }
        }
    } else {
        var50 = 0.030284086;
    }
    double var51;
    if (input[1] < 8.193793) {
        if (input[2] < 0.84043145) {
            var51 = -0.049376883;
        } else {
            var51 = 0.03713824;
        }
    } else {
        if (input[1] < 12.016938) {
            var51 = 0.050647665;
        } else {
            var51 = -0.010048885;
        }
    }
    double var52;
    if (input[3] < 0.28021672) {
        if (input[4] < 320.62726) {
            var52 = -0.037232406;
        } else {
            var52 = 0.013799241;
        }
    } else {
        if (input[1] < 9.923827) {
            var52 = -0.007708148;
        } else {
            var52 = 0.04555247;
        }
    }
    double var53;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.496991) {
            var53 = 0.031645786;
        } else {
            if (input[4] < 244.546) {
                var53 = 0.031224918;
            } else {
                var53 = -0.051636733;
            }
        }
    } else {
        var53 = 0.03174056;
    }
    double var54;
    if (input[3] < 0.43504387) {
        if (input[2] < 0.36410525) {
            var54 = 0.024455776;
        } else {
            if (input[4] < 277.82837) {
                var54 = 0.014140569;
            } else {
                var54 = -0.04709126;
            }
        }
    } else {
        var54 = 0.034656156;
    }
    double var55;
    if (input[4] < 260.28107) {
        var55 = -0.023495253;
    } else {
        if (input[0] < 7.0342813) {
            var55 = -0.013049365;
        } else {
            var55 = 0.046275746;
        }
    }
    double var56;
    if (input[0] < 7.252023) {
        if (input[0] < 7.022786) {
            if (input[0] < 6.642824) {
                var56 = 0.026437052;
            } else {
                var56 = -0.039012626;
            }
        } else {
            var56 = 0.049787525;
        }
    } else {
        var56 = -0.023947688;
    }
    double var57;
    if (input[1] < 14.244712) {
        if (input[1] < 5.1737514) {
            var57 = 0.017182522;
        } else {
            if (input[3] < 0.29139596) {
                var57 = -0.058821667;
            } else {
                var57 = 0.009039788;
            }
        }
    } else {
        var57 = 0.030469587;
    }
    double var58;
    if (input[0] < 7.4796352) {
        if (input[0] < 7.101732) {
            if (input[0] < 6.882923) {
                var58 = -0.008430889;
            } else {
                var58 = 0.034683295;
            }
        } else {
            var58 = -0.045769494;
        }
    } else {
        var58 = 0.028004346;
    }
    double var59;
    if (input[3] < 0.43504387) {
        if (input[4] < 231.67001) {
            var59 = 0.023462985;
        } else {
            if (input[0] < 6.595851) {
                var59 = 0.021632692;
            } else {
                var59 = -0.042305797;
            }
        }
    } else {
        var59 = 0.02784785;
    }
    double var60;
    if (input[4] < 260.28107) {
        var60 = -0.02182732;
    } else {
        if (input[0] < 7.0342813) {
            var60 = -0.012881028;
        } else {
            var60 = 0.041784458;
        }
    }
    double var61;
    if (input[1] < 14.244712) {
        if (input[2] < 0.4278389) {
            var61 = 0.020528326;
        } else {
            if (input[1] < 6.0616684) {
                var61 = 0.008225488;
            } else {
                var61 = -0.049680915;
            }
        }
    } else {
        var61 = 0.027584584;
    }
    double var62;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var62 = -0.050140385;
        } else {
            var62 = 0.02729932;
        }
    } else {
        if (input[2] < 0.9336739) {
            var62 = 0.040167585;
        } else {
            var62 = -0.009711579;
        }
    }
    double var63;
    if (input[1] < 8.193793) {
        if (input[2] < 0.8075296) {
            var63 = -0.041328605;
        } else {
            var63 = 0.025509471;
        }
    } else {
        if (input[2] < 0.69105196) {
            var63 = 0.042717114;
        } else {
            var63 = -0.017063681;
        }
    }
    double var64;
    if (input[0] < 7.259673) {
        if (input[3] < 0.253969) {
            var64 = -0.02178904;
        } else {
            if (input[4] < 269.8215) {
                var64 = 0.06073437;
            } else {
                var64 = -0.0064944117;
            }
        }
    } else {
        var64 = -0.020676665;
    }
    double var65;
    if (input[0] < 7.4796352) {
        if (input[0] < 7.101732) {
            if (input[3] < 0.29894865) {
                var65 = 0.025227679;
            } else {
                var65 = -0.01733725;
            }
        } else {
            var65 = -0.040916227;
        }
    } else {
        var65 = 0.027588313;
    }
    double var66;
    if (input[4] < 260.28107) {
        var66 = -0.01959363;
    } else {
        if (input[0] < 7.0342813) {
            var66 = -0.014374743;
        } else {
            var66 = 0.03739237;
        }
    }
    double var67;
    if (input[0] < 7.259673) {
        if (input[3] < 0.253969) {
            var67 = -0.020361416;
        } else {
            if (input[4] < 269.8215) {
                var67 = 0.055134855;
            } else {
                var67 = -0.0038487788;
            }
        }
    } else {
        var67 = -0.021925287;
    }
    double var68;
    if (input[4] < 260.28107) {
        var68 = -0.0188633;
    } else {
        if (input[0] < 6.595851) {
            var68 = 0.041134767;
        } else {
            if (input[0] < 7.1484923) {
                var68 = -0.043152403;
            } else {
                var68 = 0.028677637;
            }
        }
    }
    double var69;
    if (input[0] < 7.259673) {
        if (input[0] < 7.022786) {
            if (input[0] < 6.6742) {
                var69 = 0.016492037;
            } else {
                var69 = -0.032777622;
            }
        } else {
            var69 = 0.041101567;
        }
    } else {
        var69 = -0.020368114;
    }
    double var70;
    if (input[1] < 14.244712) {
        if (input[2] < 0.47721806) {
            var70 = 0.020734608;
        } else {
            if (input[4] < 271.26974) {
                var70 = 0.0059330002;
            } else {
                var70 = -0.046165958;
            }
        }
    } else {
        var70 = 0.02417583;
    }
    double var71;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var71 = -0.043284386;
        } else {
            var71 = 0.021606194;
        }
    } else {
        if (input[2] < 0.9336739) {
            var71 = 0.034788236;
        } else {
            var71 = -0.007959081;
        }
    }
    double var72;
    if (input[2] < 1.0563084) {
        if (input[1] < 7.247814) {
            var72 = -0.045560025;
        } else {
            if (input[0] < 7.022786) {
                var72 = -0.012259431;
            } else {
                var72 = 0.05294257;
            }
        }
    } else {
        var72 = 0.023763599;
    }
    double var73;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.9349284) {
            if (input[4] < 309.10547) {
                var73 = -0.0028711418;
            } else {
                var73 = 0.030150415;
            }
        } else {
            var73 = -0.034900356;
        }
    } else {
        var73 = 0.025485357;
    }
    double var74;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var74 = -0.029794058;
        } else {
            var74 = 0.0056478316;
        }
    } else {
        if (input[2] < 0.8300256) {
            var74 = 0.034463547;
        } else {
            var74 = -0.015741333;
        }
    }
    double var75;
    if (input[1] < 5.1737514) {
        var75 = 0.019147221;
    } else {
        if (input[4] < 267.10275) {
            var75 = -0.042150013;
        } else {
            if (input[4] < 315.80923) {
                var75 = 0.057281427;
            } else {
                var75 = -0.032376662;
            }
        }
    }
    double var76;
    if (input[4] < 344.44946) {
        if (input[0] < 7.202491) {
            if (input[4] < 276.47925) {
                var76 = 0.03475174;
            } else {
                var76 = -0.0206263;
            }
        } else {
            var76 = -0.03514591;
        }
    } else {
        var76 = 0.02308779;
    }
    double var77;
    if (input[0] < 7.4796352) {
        if (input[2] < 1.0563084) {
            if (input[1] < 8.193793) {
                var77 = -0.059969023;
            } else {
                var77 = 0.01831608;
            }
        } else {
            var77 = 0.02223396;
        }
    } else {
        var77 = 0.024798105;
    }
    double var78;
    if (input[1] < 5.1737514) {
        var78 = 0.018978976;
    } else {
        if (input[2] < 0.8436912) {
            if (input[2] < 0.5217849) {
                var78 = -0.036109332;
            } else {
                var78 = 0.055025935;
            }
        } else {
            var78 = -0.043365728;
        }
    }
    double var79;
    if (input[2] < 0.4278389) {
        var79 = 0.022119503;
    } else {
        if (input[2] < 1.0563084) {
            if (input[1] < 7.678836) {
                var79 = -0.055975392;
            } else {
                var79 = 0.0069210036;
            }
        } else {
            var79 = 0.019997431;
        }
    }
    double var80;
    if (input[1] < 12.016938) {
        if (input[2] < 0.47721806) {
            var80 = 0.034594256;
        } else {
            if (input[2] < 0.84043145) {
                var80 = -0.034143873;
            } else {
                var80 = 0.017510034;
            }
        }
    } else {
        var80 = -0.019975971;
    }
    double var81;
    if (input[3] < 0.28021672) {
        if (input[0] < 6.8882685) {
            var81 = -0.028796798;
        } else {
            var81 = 0.0046820585;
        }
    } else {
        if (input[2] < 0.8300256) {
            var81 = 0.029006293;
        } else {
            var81 = -0.013563967;
        }
    }
    double var82;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var82 = -0.03906907;
        } else {
            var82 = 0.019902725;
        }
    } else {
        if (input[1] < 8.578742) {
            var82 = 0.030730156;
        } else {
            var82 = -0.014485504;
        }
    }
    double var83;
    if (input[1] < 14.244712) {
        if (input[2] < 0.47721806) {
            var83 = 0.018687008;
        } else {
            if (input[4] < 271.26974) {
                var83 = 0.0031090688;
            } else {
                var83 = -0.04160174;
            }
        }
    } else {
        var83 = 0.0196537;
    }
    double var84;
    if (input[0] < 6.595851) {
        var84 = 0.019460939;
    } else {
        if (input[3] < 0.2597581) {
            var84 = 0.037486885;
        } else {
            if (input[3] < 0.40622994) {
                var84 = -0.047433652;
            } else {
                var84 = -0.0029912803;
            }
        }
    }
    double var85;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.6257324) {
            var85 = -0.027438927;
        } else {
            var85 = 0.0005203021;
        }
    } else {
        if (input[2] < 0.8300256) {
            var85 = 0.028512638;
        } else {
            var85 = -0.008963849;
        }
    }
    double var86;
    if (input[3] < 0.28021672) {
        if (input[0] < 6.8882685) {
            var86 = -0.025807954;
        } else {
            var86 = 0.0026185084;
        }
    } else {
        if (input[3] < 0.37695396) {
            var86 = 0.025782967;
        } else {
            var86 = -0.007273188;
        }
    }
    double var87;
    if (input[0] < 6.595851) {
        var87 = 0.018871345;
    } else {
        if (input[3] < 0.2597581) {
            var87 = 0.03397099;
        } else {
            if (input[0] < 7.1305275) {
                var87 = -0.04769809;
            } else {
                var87 = -0.005256879;
            }
        }
    }
    double var88;
    if (input[3] < 0.28021672) {
        if (input[4] < 311.83893) {
            var88 = -0.025859008;
        } else {
            var88 = 0.0017503769;
        }
    } else {
        if (input[2] < 0.8300256) {
            var88 = 0.025044654;
        } else {
            var88 = -0.0067338455;
        }
    }
    double var89;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var89 = -0.035314888;
        } else {
            var89 = 0.014646352;
        }
    } else {
        if (input[1] < 8.578742) {
            var89 = 0.02980447;
        } else {
            var89 = -0.012281519;
        }
    }
    double var90;
    if (input[0] < 6.9426317) {
        if (input[2] < 0.7709072) {
            var90 = -0.0033905434;
        } else {
            var90 = 0.025507879;
        }
    } else {
        if (input[3] < 0.31537604) {
            var90 = -0.03623286;
        } else {
            var90 = 0.014539247;
        }
    }
    double var91;
    if (input[1] < 14.244712) {
        if (input[2] < 0.47721806) {
            var91 = 0.018555455;
        } else {
            if (input[4] < 271.26974) {
                var91 = 0.0036730822;
            } else {
                var91 = -0.0405712;
            }
        }
    } else {
        var91 = 0.018565748;
    }
    double var92;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.805004) {
            if (input[2] < 0.49546847) {
                var92 = -0.0067669726;
            } else {
                var92 = -0.042001326;
            }
        } else {
            var92 = 0.022040747;
        }
    } else {
        var92 = 0.017967535;
    }
    double var93;
    if (input[1] < 12.016938) {
        if (input[1] < 7.247814) {
            if (input[2] < 0.73044044) {
                var93 = -0.029176144;
            } else {
                var93 = 0.020830533;
            }
        } else {
            var93 = 0.030464737;
        }
    } else {
        var93 = -0.019674506;
    }
    double var94;
    if (input[1] < 6.0616684) {
        if (input[1] < 4.1175404) {
            var94 = -0.0032193477;
        } else {
            var94 = 0.026536763;
        }
    } else {
        if (input[2] < 0.69105196) {
            var94 = 0.01187346;
        } else {
            var94 = -0.035069745;
        }
    }
    double var95;
    if (input[1] < 5.1737514) {
        var95 = 0.015422236;
    } else {
        if (input[2] < 0.5217849) {
            var95 = -0.041303314;
        } else {
            if (input[2] < 0.8436912) {
                var95 = 0.05118023;
            } else {
                var95 = -0.031207362;
            }
        }
    }
    double var96;
    if (input[1] < 14.244712) {
        if (input[2] < 0.47721806) {
            var96 = 0.017767439;
        } else {
            if (input[1] < 6.0616684) {
                var96 = -0.000371349;
            } else {
                var96 = -0.03854408;
            }
        }
    } else {
        var96 = 0.018629026;
    }
    double var97;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.805004) {
            if (input[2] < 0.49546847) {
                var97 = -0.005956037;
            } else {
                var97 = -0.040607236;
            }
        } else {
            var97 = 0.019432139;
        }
    } else {
        var97 = 0.0187556;
    }
    double var98;
    if (input[1] < 12.016938) {
        if (input[1] < 7.247814) {
            if (input[2] < 0.73044044) {
                var98 = -0.026723582;
            } else {
                var98 = 0.016008286;
            }
        } else {
            var98 = 0.030426422;
        }
    } else {
        var98 = -0.017871642;
    }
    double var99;
    if (input[1] < 5.1737514) {
        var99 = 0.014385312;
    } else {
        if (input[2] < 0.5125254) {
            var99 = -0.038693268;
        } else {
            if (input[2] < 0.8436912) {
                var99 = 0.045804776;
            } else {
                var99 = -0.027856274;
            }
        }
    }
    double var100;
    var100 = sigmoid(var0 + var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10 + var11 + var12 + var13 + var14 + var15 + var16 + var17 + var18 + var19 + var20 + var21 + var22 + var23 + var24 + var25 + var26 + var27 + var28 + var29 + var30 + var31 + var32 + var33 + var34 + var35 + var36 + var37 + var38 + var39 + var40 + var41 + var42 + var43 + var44 + var45 + var46 + var47 + var48 + var49 + var50 + var51 + var52 + var53 + var54 + var55 + var56 + var57 + var58 + var59 + var60 + var61 + var62 + var63 + var64 + var65 + var66 + var67 + var68 + var69 + var70 + var71 + var72 + var73 + var74 + var75 + var76 + var77 + var78 + var79 + var80 + var81 + var82 + var83 + var84 + var85 + var86 + var87 + var88 + var89 + var90 + var91 + var92 + var93 + var94 + var95 + var96 + var97 + var98 + var99);
    memcpy(output, (double[]){1.0 - var100, var100}, 2 * sizeof(double));
}
