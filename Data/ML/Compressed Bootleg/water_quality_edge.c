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
                if (input[0] < 6.275958) {
                    var0 = 0.32500002;
                } else {
                    if (input[4] < 208.13354) {
                        var0 = 0.21951221;
                    } else {
                        if (input[2] < 0.33858895) {
                            var0 = 0.051851857;
                        } else {
                            var0 = -0.49743593;
                        }
                    }
                }
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
            if (input[1] < 23.513678) {
                if (input[0] < 6.2425766) {
                    var1 = 0.29238245;
                } else {
                    if (input[4] < 203.5464) {
                        var1 = 0.27922973;
                    } else {
                        if (input[2] < 0.29095724) {
                            var1 = 0.145286;
                        } else {
                            var1 = -0.41566235;
                        }
                    }
                }
            } else {
                var1 = 0.34001833;
            }
        } else {
            var1 = 0.3613395;
        }
    } else {
        var1 = 0.38823482;
    }
    double var2;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[1] < 25.119394) {
                if (input[0] < 6.275958) {
                    var2 = 0.24801694;
                } else {
                    if (input[2] < 0.2584414) {
                        var2 = 0.2629517;
                    } else {
                        if (input[4] < 208.13354) {
                            var2 = 0.17167023;
                        } else {
                            var2 = -0.37374282;
                        }
                    }
                }
            } else {
                var2 = 0.29959604;
            }
        } else {
            var2 = 0.30819684;
        }
    } else {
        var2 = 0.33150938;
    }
    double var3;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[1] < 25.119394) {
                if (input[0] < 6.275958) {
                    var3 = 0.21648222;
                } else {
                    if (input[2] < 0.2584414) {
                        var3 = 0.23093103;
                    } else {
                        if (input[4] < 208.13354) {
                            var3 = 0.14887139;
                        } else {
                            var3 = -0.32773596;
                        }
                    }
                }
            } else {
                var3 = 0.26324916;
            }
        } else {
            var3 = 0.27077517;
        }
    } else {
        var3 = 0.29275596;
    }
    double var4;
    if (input[3] < 0.49971524) {
        if (input[1] < 9.452143) {
            if (input[0] < 7.6843157) {
                if (input[4] < 231.1042) {
                    var4 = 0.05521872;
                } else {
                    if (input[0] < 6.7278085) {
                        var4 = -0.013832101;
                    } else {
                        var4 = -0.1719242;
                    }
                }
            } else {
                var4 = 0.19439216;
            }
        } else {
            if (input[3] < 0.2415994) {
                var4 = 0.035526976;
            } else {
                var4 = 0.20802934;
            }
        }
    } else {
        var4 = 0.26319712;
    }
    double var5;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[1] < 25.119394) {
                if (input[0] < 6.275958) {
                    var5 = 0.18085003;
                } else {
                    if (input[2] < 0.27287546) {
                        var5 = 0.14868888;
                    } else {
                        if (input[4] < 214.56258) {
                            var5 = 0.096916184;
                        } else {
                            var5 = -0.28190553;
                        }
                    }
                }
            } else {
                var5 = 0.21738343;
            }
        } else {
            var5 = 0.22487722;
        }
    } else {
        var5 = 0.23892145;
    }
    double var6;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[1] < 25.119394) {
                if (input[0] < 6.3477654) {
                    var6 = 0.14798094;
                } else {
                    if (input[2] < 0.2808891) {
                        var6 = 0.1193329;
                    } else {
                        if (input[4] < 218.20956) {
                            var6 = 0.07212307;
                        } else {
                            var6 = -0.2508728;
                        }
                    }
                }
            } else {
                var6 = 0.19706042;
            }
        } else {
            var6 = 0.20390758;
        }
    } else {
        var6 = 0.21802115;
    }
    double var7;
    if (input[3] < 0.49971524) {
        if (input[0] < 7.761515) {
            if (input[1] < 25.119394) {
                if (input[0] < 6.399852) {
                    var7 = 0.1189723;
                } else {
                    if (input[4] < 214.56258) {
                        var7 = 0.101200856;
                    } else {
                        if (input[2] < 0.33858895) {
                            var7 = 0.033929374;
                        } else {
                            var7 = -0.22078699;
                        }
                    }
                }
            } else {
                var7 = 0.17953172;
            }
        } else {
            var7 = 0.18578471;
        }
    } else {
        var7 = 0.19952992;
    }
    double var8;
    if (input[1] < 9.312289) {
        if (input[3] < 0.44943362) {
            if (input[0] < 7.43616) {
                if (input[2] < 0.73044044) {
                    var8 = -0.09720685;
                } else {
                    var8 = 0.021891609;
                }
            } else {
                var8 = 0.10339064;
            }
        } else {
            var8 = 0.13009693;
        }
    } else {
        var8 = 0.15368141;
    }
    double var9;
    if (input[3] < 0.49971524) {
        if (input[0] < 6.2990746) {
            var9 = 0.14467406;
        } else {
            if (input[0] < 7.4796352) {
                if (input[1] < 14.244712) {
                    if (input[4] < 240.33904) {
                        var9 = 0.019119093;
                    } else {
                        var9 = -0.12494424;
                    }
                } else {
                    var9 = 0.055869404;
                }
            } else {
                var9 = 0.12361204;
            }
        }
    } else {
        var9 = 0.17154647;
    }
    double var10;
    if (input[3] < 0.31634185) {
        if (input[3] < 0.2597581) {
            if (input[0] < 7.0342813) {
                var10 = 0.010528016;
            } else {
                var10 = 0.07714779;
            }
        } else {
            var10 = -0.010400458;
        }
    } else {
        var10 = 0.12252186;
    }
    double var11;
    if (input[3] < 0.4843025) {
        if (input[1] < 9.452143) {
            if (input[1] < 5.1737514) {
                var11 = 0.041224092;
            } else {
                var11 = -0.07272407;
            }
        } else {
            if (input[0] < 6.6163263) {
                var11 = 0.11698952;
            } else {
                var11 = 0.023706531;
            }
        }
    } else {
        var11 = 0.13642992;
    }
    double var12;
    if (input[0] < 7.6843157) {
        if (input[0] < 6.642824) {
            if (input[3] < 0.29175043) {
                var12 = 0.020703819;
            } else {
                var12 = 0.12613021;
            }
        } else {
            if (input[4] < 245.96275) {
                var12 = 0.055449266;
            } else {
                if (input[3] < 0.339839) {
                    var12 = -0.099739656;
                } else {
                    var12 = 0.009649094;
                }
            }
        }
    } else {
        var12 = 0.11684973;
    }
    double var13;
    if (input[1] < 8.193793) {
        if (input[1] < 4.9135017) {
            if (input[1] < 3.4090004) {
                var13 = -0.0033357523;
            } else {
                var13 = 0.08399426;
            }
        } else {
            var13 = -0.0560738;
        }
    } else {
        if (input[2] < 0.83799225) {
            var13 = 0.10395341;
        } else {
            var13 = 0.006377725;
        }
    }
    double var14;
    if (input[3] < 0.449517) {
        if (input[0] < 7.528561) {
            if (input[0] < 6.6163263) {
                var14 = 0.060883116;
            } else {
                if (input[4] < 267.10275) {
                    var14 = -0.004826551;
                } else {
                    var14 = -0.08896874;
                }
            }
        } else {
            var14 = 0.08571146;
        }
    } else {
        var14 = 0.10277104;
    }
    double var15;
    if (input[2] < 0.4278389) {
        if (input[4] < 310.4005) {
            var15 = 0.022504425;
        } else {
            var15 = 0.09294093;
        }
    } else {
        if (input[1] < 14.244712) {
            if (input[4] < 247.97218) {
                var15 = 0.019782744;
            } else {
                var15 = -0.056135956;
            }
        } else {
            var15 = 0.07247999;
        }
    }
    double var16;
    if (input[3] < 0.4430559) {
        if (input[0] < 7.477571) {
            if (input[0] < 6.595851) {
                var16 = 0.044533204;
            } else {
                if (input[3] < 0.28543997) {
                    var16 = -0.0045456416;
                } else {
                    var16 = -0.08673635;
                }
            }
        } else {
            var16 = 0.06939253;
        }
    } else {
        var16 = 0.08639345;
    }
    double var17;
    if (input[3] < 0.4430559) {
        if (input[1] < 14.244712) {
            if (input[2] < 0.3854102) {
                var17 = 0.041459925;
            } else {
                if (input[2] < 0.7709072) {
                    var17 = -0.07731897;
                } else {
                    var17 = -0.002493623;
                }
            }
        } else {
            var17 = 0.058941554;
        }
    } else {
        var17 = 0.075243734;
    }
    double var18;
    if (input[0] < 7.528561) {
        if (input[0] < 6.642824) {
            var18 = 0.056160912;
        } else {
            if (input[4] < 242.76364) {
                var18 = 0.025589371;
            } else {
                var18 = -0.0605465;
            }
        }
    } else {
        var18 = 0.066626765;
    }
    double var19;
    if (input[3] < 0.31634185) {
        if (input[4] < 318.22913) {
            var19 = -0.03872414;
        } else {
            var19 = 0.0357638;
        }
    } else {
        if (input[3] < 0.43504387) {
            var19 = 0.017696025;
        } else {
            var19 = 0.06325894;
        }
    }
    double var20;
    if (input[1] < 17.442425) {
        if (input[2] < 0.40490842) {
            var20 = 0.05089098;
        } else {
            if (input[4] < 247.97218) {
                var20 = 0.017079229;
            } else {
                var20 = -0.054760903;
            }
        }
    } else {
        var20 = 0.060859773;
    }
    double var21;
    if (input[1] < 8.193793) {
        if (input[1] < 4.8317194) {
            var21 = 0.028408533;
        } else {
            var21 = -0.056782957;
        }
    } else {
        if (input[3] < 0.28021672) {
            var21 = -0.0030569492;
        } else {
            var21 = 0.060463373;
        }
    }
    double var22;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.595851) {
            var22 = 0.045807827;
        } else {
            if (input[4] < 245.96275) {
                var22 = 0.02586924;
            } else {
                var22 = -0.06605123;
            }
        }
    } else {
        var22 = 0.050303698;
    }
    double var23;
    if (input[3] < 0.411422) {
        if (input[1] < 8.441515) {
            if (input[2] < 0.65712863) {
                var23 = -0.07398896;
            } else {
                var23 = 0.020230189;
            }
        } else {
            if (input[0] < 6.9038196) {
                var23 = -0.004945075;
            } else {
                var23 = 0.046192776;
            }
        }
    } else {
        var23 = 0.047248103;
    }
    double var24;
    if (input[2] < 0.4278389) {
        var24 = 0.040946502;
    } else {
        if (input[0] < 6.7654123) {
            var24 = 0.03156164;
        } else {
            var24 = -0.04306566;
        }
    }
    double var25;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.595851) {
            var25 = 0.03311846;
        } else {
            if (input[4] < 248.23346) {
                var25 = 0.018207822;
            } else {
                var25 = -0.05567467;
            }
        }
    } else {
        var25 = 0.043501303;
    }
    double var26;
    if (input[1] < 14.244712) {
        if (input[2] < 0.4278389) {
            var26 = 0.030715523;
        } else {
            if (input[1] < 5.0043106) {
                var26 = 0.0023767469;
            } else {
                var26 = -0.05030058;
            }
        }
    } else {
        var26 = 0.04218056;
    }
    double var27;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var27 = -0.045088265;
        } else {
            var27 = 0.012842163;
        }
    } else {
        if (input[1] < 9.923827) {
            var27 = -0.0010263782;
        } else {
            var27 = 0.051078063;
        }
    }
    double var28;
    if (input[4] < 330.03995) {
        if (input[2] < 0.6516473) {
            var28 = -0.04537178;
        } else {
            var28 = 0.022697039;
        }
    } else {
        var28 = 0.036761973;
    }
    double var29;
    if (input[3] < 0.411422) {
        if (input[1] < 8.441515) {
            var29 = -0.034912065;
        } else {
            if (input[2] < 0.66381705) {
                var29 = 0.039786257;
            } else {
                var29 = -0.0129896775;
            }
        }
    } else {
        var29 = 0.03843286;
    }
    double var30;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.595851) {
            var30 = 0.025569111;
        } else {
            if (input[4] < 250.17334) {
                var30 = 0.013189113;
            } else {
                var30 = -0.05196191;
            }
        }
    } else {
        var30 = 0.0391699;
    }
    double var31;
    if (input[2] < 0.4278389) {
        var31 = 0.031443954;
    } else {
        if (input[0] < 6.7654123) {
            var31 = 0.018909277;
        } else {
            var31 = -0.03494407;
        }
    }
    double var32;
    if (input[3] < 0.28021672) {
        if (input[0] < 6.8882685) {
            var32 = -0.047145627;
        } else {
            var32 = 0.016534718;
        }
    } else {
        if (input[2] < 0.8300256) {
            var32 = 0.038368896;
        } else {
            var32 = -0.00952625;
        }
    }
    double var33;
    if (input[4] < 330.03995) {
        if (input[2] < 0.6516473) {
            var33 = -0.046553478;
        } else {
            var33 = 0.022611376;
        }
    } else {
        var33 = 0.03061091;
    }
    double var34;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.496991) {
            var34 = 0.025099797;
        } else {
            if (input[4] < 242.76364) {
                var34 = 0.02429233;
            } else {
                var34 = -0.05102345;
            }
        }
    } else {
        var34 = 0.032489054;
    }
    double var35;
    if (input[3] < 0.411422) {
        if (input[1] < 8.441515) {
            var35 = -0.03292208;
        } else {
            var35 = 0.016336216;
        }
    } else {
        var35 = 0.032859556;
    }
    double var36;
    if (input[2] < 0.4278389) {
        var36 = 0.026998777;
    } else {
        if (input[2] < 1.0563084) {
            if (input[1] < 9.923827) {
                var36 = -0.054230426;
            } else {
                var36 = 0.0076223426;
            }
        } else {
            var36 = 0.023071557;
        }
    }
    double var37;
    if (input[4] < 330.03995) {
        if (input[2] < 0.6516473) {
            var37 = -0.039885543;
        } else {
            var37 = 0.018407034;
        }
    } else {
        var37 = 0.027540395;
    }
    double var38;
    if (input[0] < 7.006296) {
        if (input[0] < 6.642824) {
            var38 = 0.016662894;
        } else {
            var38 = -0.048305895;
        }
    } else {
        if (input[0] < 7.259673) {
            var38 = 0.052429378;
        } else {
            var38 = -0.015798913;
        }
    }
    double var39;
    if (input[0] < 7.4796352) {
        if (input[3] < 0.253969) {
            var39 = -0.038277734;
        } else {
            if (input[0] < 6.7654123) {
                var39 = 0.050332427;
            } else {
                var39 = -0.032916155;
            }
        }
    } else {
        var39 = 0.03162328;
    }
    double var40;
    if (input[0] < 6.882923) {
        var40 = -0.019923436;
    } else {
        if (input[0] < 7.252023) {
            var40 = 0.04483041;
        } else {
            var40 = -0.017509978;
        }
    }
    double var41;
    if (input[0] < 7.4796352) {
        if (input[0] < 6.595851) {
            var41 = 0.0167131;
        } else {
            if (input[3] < 0.28543997) {
                var41 = 0.010416025;
            } else {
                var41 = -0.04297463;
            }
        }
    } else {
        var41 = 0.029601224;
    }
    double var42;
    if (input[3] < 0.28021672) {
        if (input[0] < 6.8882685) {
            var42 = -0.04075748;
        } else {
            var42 = 0.009803691;
        }
    } else {
        if (input[2] < 0.8300256) {
            var42 = 0.03795696;
        } else {
            var42 = -0.013789305;
        }
    }
    double var43;
    if (input[3] < 0.411422) {
        if (input[4] < 249.89142) {
            var43 = 0.02121744;
        } else {
            if (input[4] < 330.03995) {
                var43 = -0.049828343;
            } else {
                var43 = 0.013986461;
            }
        }
    } else {
        var43 = 0.02868565;
    }
    double var44;
    if (input[1] < 14.244712) {
        if (input[1] < 5.1737514) {
            var44 = 0.0181232;
        } else {
            var44 = -0.033198748;
        }
    } else {
        var44 = 0.02768016;
    }
    double var45;
    if (input[2] < 0.4278389) {
        var45 = 0.021576857;
    } else {
        if (input[0] < 6.7654123) {
            var45 = 0.01782301;
        } else {
            var45 = -0.031378772;
        }
    }
    double var46;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var46 = -0.037771784;
        } else {
            var46 = 0.01192762;
        }
    } else {
        if (input[2] < 0.8300256) {
            var46 = 0.031249788;
        } else {
            var46 = -0.010885033;
        }
    }
    double var47;
    if (input[0] < 7.022786) {
        if (input[0] < 6.642824) {
            var47 = 0.0143336505;
        } else {
            var47 = -0.04108495;
        }
    } else {
        if (input[1] < 7.5670624) {
            var47 = -0.005717156;
        } else {
            var47 = 0.034463525;
        }
    }
    double var48;
    if (input[1] < 14.244712) {
        if (input[2] < 0.4278389) {
            var48 = 0.019036867;
        } else {
            if (input[1] < 6.0616684) {
                var48 = 0.0061705573;
            } else {
                var48 = -0.049379025;
            }
        }
    } else {
        var48 = 0.023286361;
    }
    double var49;
    if (input[2] < 0.6516473) {
        if (input[4] < 310.4005) {
            var49 = -0.054512467;
        } else {
            var49 = 0.034068923;
        }
    } else {
        if (input[4] < 274.24533) {
            var49 = 0.048290852;
        } else {
            var49 = -0.020876804;
        }
    }
    double var50;
    if (input[0] < 6.882923) {
        var50 = -0.016668549;
    } else {
        if (input[0] < 7.252023) {
            var50 = 0.037145898;
        } else {
            var50 = -0.016083442;
        }
    }
    double var51;
    if (input[0] < 7.477571) {
        if (input[0] < 6.595851) {
            var51 = 0.016727606;
        } else {
            if (input[4] < 276.47925) {
                var51 = 0.011114493;
            } else {
                var51 = -0.047597606;
            }
        }
    } else {
        var51 = 0.024841074;
    }
    double var52;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var52 = -0.0324029;
        } else {
            var52 = 0.00853586;
        }
    } else {
        if (input[2] < 0.8300256) {
            var52 = 0.027815467;
        } else {
            var52 = -0.009845666;
        }
    }
    double var53;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.193793) {
            var53 = -0.041810244;
        } else {
            var53 = 0.026430493;
        }
    } else {
        var53 = 0.022363253;
    }
    double var54;
    if (input[0] < 7.477571) {
        if (input[3] < 0.253969) {
            var54 = -0.031830613;
        } else {
            if (input[0] < 6.7654123) {
                var54 = 0.043932185;
            } else {
                var54 = -0.029342076;
            }
        }
    } else {
        var54 = 0.024012225;
    }
    double var55;
    if (input[0] < 6.882923) {
        var55 = -0.019029032;
    } else {
        if (input[0] < 7.252023) {
            var55 = 0.03886897;
        } else {
            var55 = -0.015106427;
        }
    }
    double var56;
    if (input[2] < 0.4278389) {
        var56 = 0.020271823;
    } else {
        if (input[2] < 1.0563084) {
            if (input[1] < 9.649728) {
                var56 = -0.03900286;
            } else {
                var56 = -0.0034428816;
            }
        } else {
            var56 = 0.01973093;
        }
    }
    double var57;
    if (input[1] < 5.1737514) {
        var57 = 0.01803944;
    } else {
        if (input[0] < 7.022786) {
            var57 = -0.033064477;
        } else {
            var57 = 0.016449949;
        }
    }
    double var58;
    if (input[4] < 310.4005) {
        if (input[2] < 0.6516473) {
            var58 = -0.046535138;
        } else {
            var58 = 0.022951972;
        }
    } else {
        var58 = 0.017542792;
    }
    double var59;
    if (input[2] < 0.4278389) {
        var59 = 0.018574802;
    } else {
        if (input[4] < 281.0356) {
            var59 = 0.011473922;
        } else {
            var59 = -0.03114891;
        }
    }
    double var60;
    if (input[4] < 310.4005) {
        if (input[2] < 0.6516473) {
            var60 = -0.040847763;
        } else {
            var60 = 0.018482028;
        }
    } else {
        var60 = 0.016328774;
    }
    double var61;
    if (input[2] < 0.9336739) {
        if (input[0] < 6.882923) {
            var61 = -0.03209571;
        } else {
            if (input[0] < 7.2064657) {
                var61 = 0.05894996;
            } else {
                var61 = -0.0023458886;
            }
        }
    } else {
        var61 = -0.020699264;
    }
    double var62;
    if (input[0] < 6.595851) {
        var62 = 0.02095908;
    } else {
        if (input[3] < 0.2597581) {
            var62 = 0.038505632;
        } else {
            if (input[0] < 7.1305275) {
                var62 = -0.051897515;
            } else {
                var62 = -0.00818217;
            }
        }
    }
    double var63;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var63 = -0.028455684;
        } else {
            var63 = 0.0017522477;
        }
    } else {
        if (input[2] < 0.8300256) {
            var63 = 0.029477624;
        } else {
            var63 = -0.010698224;
        }
    }
    double var64;
    if (input[1] < 14.244712) {
        if (input[1] < 5.1737514) {
            var64 = 0.01434643;
        } else {
            var64 = -0.028095653;
        }
    } else {
        var64 = 0.020081025;
    }
    double var65;
    if (input[3] < 0.28021672) {
        if (input[2] < 0.5814099) {
            var65 = -0.023956897;
        } else {
            var65 = 0.0015327781;
        }
    } else {
        if (input[0] < 6.9200306) {
            var65 = 0.032243796;
        } else {
            var65 = -0.0076419325;
        }
    }
    double var66;
    if (input[0] < 7.477571) {
        if (input[0] < 6.595851) {
            var66 = 0.016680686;
        } else {
            if (input[4] < 276.47925) {
                var66 = 0.008101055;
            } else {
                var66 = -0.045074265;
            }
        }
    } else {
        var66 = 0.023222145;
    }
    double var67;
    if (input[2] < 0.4278389) {
        var67 = 0.019052021;
    } else {
        if (input[0] < 6.7654123) {
            var67 = 0.012978139;
        } else {
            var67 = -0.027947359;
        }
    }
    double var68;
    if (input[0] < 6.882923) {
        var68 = -0.015826711;
    } else {
        if (input[0] < 7.252023) {
            var68 = 0.032215577;
        } else {
            var68 = -0.012955048;
        }
    }
    double var69;
    if (input[0] < 7.475212) {
        if (input[0] < 6.9349284) {
            if (input[3] < 0.28021672) {
                var69 = -0.0088308705;
            } else {
                var69 = 0.023333412;
            }
        } else {
            var69 = -0.027106384;
        }
    } else {
        var69 = 0.020563565;
    }
    double var70;
    if (input[4] < 310.4005) {
        if (input[2] < 0.6516473) {
            var70 = -0.036271524;
        } else {
            var70 = 0.016765358;
        }
    } else {
        var70 = 0.016087906;
    }
    double var71;
    if (input[2] < 0.4278389) {
        var71 = 0.017739398;
    } else {
        if (input[4] < 281.0356) {
            var71 = 0.009773134;
        } else {
            var71 = -0.027788574;
        }
    }
    double var72;
    if (input[1] < 4.390688) {
        var72 = -0.018787486;
    } else {
        if (input[0] < 6.642824) {
            var72 = 0.040245175;
        } else {
            if (input[0] < 7.06537) {
                var72 = -0.03652805;
            } else {
                var72 = 0.01308161;
            }
        }
    }
    double var73;
    if (input[0] < 6.882923) {
        var73 = -0.017189683;
    } else {
        if (input[0] < 7.252023) {
            var73 = 0.032313585;
        } else {
            var73 = -0.012326245;
        }
    }
    double var74;
    if (input[0] < 7.475212) {
        if (input[3] < 0.28021672) {
            var74 = -0.025241852;
        } else {
            var74 = 0.00899029;
        }
    } else {
        var74 = 0.019297935;
    }
    double var75;
    if (input[1] < 14.244712) {
        if (input[2] < 0.47721806) {
            var75 = 0.015227435;
        } else {
            if (input[3] < 0.2939739) {
                var75 = 0.0007150076;
            } else {
                var75 = -0.035188626;
            }
        }
    } else {
        var75 = 0.019146908;
    }
    double var76;
    if (input[1] < 12.016938) {
        if (input[1] < 4.390688) {
            var76 = -0.015282578;
        } else {
            var76 = 0.024372375;
        }
    } else {
        var76 = -0.017286956;
    }
    double var77;
    if (input[1] < 14.244712) {
        if (input[3] < 0.31634185) {
            if (input[1] < 5.219507) {
                var77 = -0.003501712;
            } else {
                var77 = -0.034820233;
            }
        } else {
            var77 = 0.015017132;
        }
    } else {
        var77 = 0.018869663;
    }
    double var78;
    if (input[3] < 0.2597581) {
        var78 = 0.014754163;
    } else {
        if (input[0] < 6.9426317) {
            var78 = 0.020173984;
        } else {
            var78 = -0.033216767;
        }
    }
    double var79;
    if (input[0] < 7.022786) {
        if (input[0] < 6.595851) {
            var79 = 0.011021631;
        } else {
            var79 = -0.032062657;
        }
    } else {
        if (input[3] < 0.29886365) {
            var79 = -0.010372944;
        } else {
            var79 = 0.029508019;
        }
    }
    double var80;
    if (input[0] < 6.882923) {
        var80 = -0.015148476;
    } else {
        if (input[0] < 7.252023) {
            var80 = 0.02889321;
        } else {
            var80 = -0.01189988;
        }
    }
    double var81;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.805004) {
            var81 = -0.033234373;
        } else {
            var81 = 0.023582002;
        }
    } else {
        var81 = 0.018135482;
    }
    double var82;
    if (input[1] < 12.016938) {
        if (input[3] < 0.2597581) {
            var82 = 0.03177234;
        } else {
            var82 = -0.006205202;
        }
    } else {
        var82 = -0.019880706;
    }
    double var83;
    if (input[1] < 12.016938) {
        if (input[0] < 7.0051165) {
            var83 = -0.012315512;
        } else {
            var83 = 0.025486676;
        }
    } else {
        var83 = -0.016390065;
    }
    double var84;
    if (input[1] < 14.244712) {
        if (input[1] < 6.5116553) {
            var84 = 0.012118706;
        } else {
            var84 = -0.029279651;
        }
    } else {
        var84 = 0.018542709;
    }
    double var85;
    if (input[2] < 0.9336739) {
        if (input[0] < 6.882923) {
            var85 = -0.027272554;
        } else {
            if (input[0] < 7.2064657) {
                var85 = 0.050648727;
            } else {
                var85 = -0.0026475189;
            }
        }
    } else {
        var85 = -0.01608715;
    }
    double var86;
    if (input[0] < 6.7654123) {
        var86 = 0.016249146;
    } else {
        if (input[4] < 301.96783) {
            var86 = 0.0084525505;
        } else {
            var86 = -0.029901246;
        }
    }
    double var87;
    if (input[4] < 330.03995) {
        if (input[4] < 276.47925) {
            if (input[2] < 0.6806068) {
                var87 = -0.008288193;
            } else {
                var87 = 0.02234854;
            }
        } else {
            var87 = -0.029592613;
        }
    } else {
        var87 = 0.017350387;
    }
    double var88;
    if (input[4] < 260.28107) {
        var88 = -0.01593206;
    } else {
        if (input[0] < 6.6423483) {
            var88 = 0.030609244;
        } else {
            var88 = -0.006648279;
        }
    }
    double var89;
    if (input[0] < 7.43616) {
        if (input[0] < 6.9349284) {
            if (input[1] < 8.837732) {
                var89 = 0.02055693;
            } else {
                var89 = -0.0058862944;
            }
        } else {
            var89 = -0.027712068;
        }
    } else {
        var89 = 0.020273695;
    }
    double var90;
    if (input[3] < 0.28021672) {
        if (input[3] < 0.22297037) {
            var90 = 0.00018254222;
        } else {
            var90 = -0.0197285;
        }
    } else {
        if (input[2] < 0.79196477) {
            var90 = 0.023996737;
        } else {
            var90 = -0.006958417;
        }
    }
    double var91;
    if (input[1] < 14.244712) {
        if (input[3] < 0.31634185) {
            var91 = -0.022638904;
        } else {
            var91 = 0.013965247;
        }
    } else {
        var91 = 0.017602246;
    }
    double var92;
    if (input[1] < 12.016938) {
        if (input[3] < 0.2597581) {
            var92 = 0.029215008;
        } else {
            var92 = -0.007967135;
        }
    } else {
        var92 = -0.014480259;
    }
    double var93;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.805004) {
            var93 = -0.0318747;
        } else {
            var93 = 0.02454317;
        }
    } else {
        var93 = 0.01760559;
    }
    double var94;
    if (input[1] < 12.016938) {
        if (input[0] < 7.0051165) {
            var94 = -0.011229964;
        } else {
            var94 = 0.025435338;
        }
    } else {
        var94 = -0.015966743;
    }
    double var95;
    if (input[2] < 0.9336739) {
        if (input[0] < 6.882923) {
            var95 = -0.025010843;
        } else {
            if (input[0] < 7.236619) {
                var95 = 0.04596441;
            } else {
                var95 = -0.00012073379;
            }
        }
    } else {
        var95 = -0.015570009;
    }
    double var96;
    if (input[0] < 6.7654123) {
        var96 = 0.015615327;
    } else {
        if (input[4] < 301.96783) {
            var96 = 0.008187992;
        } else {
            var96 = -0.027865075;
        }
    }
    double var97;
    if (input[4] < 260.28107) {
        var97 = -0.014667441;
    } else {
        if (input[0] < 6.6742) {
            var97 = 0.026877677;
        } else {
            var97 = -0.0052718106;
        }
    }
    double var98;
    if (input[2] < 1.0563084) {
        if (input[1] < 8.805004) {
            var98 = -0.028357139;
        } else {
            var98 = 0.020481557;
        }
    } else {
        var98 = 0.01701676;
    }
    double var99;
    if (input[0] < 7.43616) {
        if (input[3] < 0.253969) {
            var99 = -0.031668276;
        } else {
            if (input[0] < 6.7654123) {
                var99 = 0.04121898;
            } else {
                var99 = -0.024444396;
            }
        }
    } else {
        var99 = 0.020696394;
    }
    double var100;
    var100 = sigmoid(var0 + var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10 + var11 + var12 + var13 + var14 + var15 + var16 + var17 + var18 + var19 + var20 + var21 + var22 + var23 + var24 + var25 + var26 + var27 + var28 + var29 + var30 + var31 + var32 + var33 + var34 + var35 + var36 + var37 + var38 + var39 + var40 + var41 + var42 + var43 + var44 + var45 + var46 + var47 + var48 + var49 + var50 + var51 + var52 + var53 + var54 + var55 + var56 + var57 + var58 + var59 + var60 + var61 + var62 + var63 + var64 + var65 + var66 + var67 + var68 + var69 + var70 + var71 + var72 + var73 + var74 + var75 + var76 + var77 + var78 + var79 + var80 + var81 + var82 + var83 + var84 + var85 + var86 + var87 + var88 + var89 + var90 + var91 + var92 + var93 + var94 + var95 + var96 + var97 + var98 + var99);
    memcpy(output, (double[]){1.0 - var100, var100}, 2 * sizeof(double));
}
