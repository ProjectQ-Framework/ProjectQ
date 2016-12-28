template <class V, class M>
inline void kernel_core(V &psi, unsigned I, unsigned d0, unsigned d1, unsigned d2, unsigned d3, unsigned d4, M const& m, M const& mt)
{
	__m256d v[4];

	v[0] = load2(&psi[I]);
	v[1] = load2(&psi[I + d0]);
	v[2] = load2(&psi[I + d1]);
	v[3] = load2(&psi[I + d0 + d1]);

	__m256d tmp[16];

	tmp[0] = add(mul(v[0], m[0], mt[0]), add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3]))));
	tmp[1] = add(mul(v[0], m[4], mt[4]), add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7]))));
	tmp[2] = add(mul(v[0], m[8], mt[8]), add(mul(v[1], m[9], mt[9]), add(mul(v[2], m[10], mt[10]), mul(v[3], m[11], mt[11]))));
	tmp[3] = add(mul(v[0], m[12], mt[12]), add(mul(v[1], m[13], mt[13]), add(mul(v[2], m[14], mt[14]), mul(v[3], m[15], mt[15]))));
	tmp[4] = add(mul(v[0], m[16], mt[16]), add(mul(v[1], m[17], mt[17]), add(mul(v[2], m[18], mt[18]), mul(v[3], m[19], mt[19]))));
	tmp[5] = add(mul(v[0], m[20], mt[20]), add(mul(v[1], m[21], mt[21]), add(mul(v[2], m[22], mt[22]), mul(v[3], m[23], mt[23]))));
	tmp[6] = add(mul(v[0], m[24], mt[24]), add(mul(v[1], m[25], mt[25]), add(mul(v[2], m[26], mt[26]), mul(v[3], m[27], mt[27]))));
	tmp[7] = add(mul(v[0], m[28], mt[28]), add(mul(v[1], m[29], mt[29]), add(mul(v[2], m[30], mt[30]), mul(v[3], m[31], mt[31]))));
	tmp[8] = add(mul(v[0], m[32], mt[32]), add(mul(v[1], m[33], mt[33]), add(mul(v[2], m[34], mt[34]), mul(v[3], m[35], mt[35]))));
	tmp[9] = add(mul(v[0], m[36], mt[36]), add(mul(v[1], m[37], mt[37]), add(mul(v[2], m[38], mt[38]), mul(v[3], m[39], mt[39]))));
	tmp[10] = add(mul(v[0], m[40], mt[40]), add(mul(v[1], m[41], mt[41]), add(mul(v[2], m[42], mt[42]), mul(v[3], m[43], mt[43]))));
	tmp[11] = add(mul(v[0], m[44], mt[44]), add(mul(v[1], m[45], mt[45]), add(mul(v[2], m[46], mt[46]), mul(v[3], m[47], mt[47]))));
	tmp[12] = add(mul(v[0], m[48], mt[48]), add(mul(v[1], m[49], mt[49]), add(mul(v[2], m[50], mt[50]), mul(v[3], m[51], mt[51]))));
	tmp[13] = add(mul(v[0], m[52], mt[52]), add(mul(v[1], m[53], mt[53]), add(mul(v[2], m[54], mt[54]), mul(v[3], m[55], mt[55]))));
	tmp[14] = add(mul(v[0], m[56], mt[56]), add(mul(v[1], m[57], mt[57]), add(mul(v[2], m[58], mt[58]), mul(v[3], m[59], mt[59]))));
	tmp[15] = add(mul(v[0], m[60], mt[60]), add(mul(v[1], m[61], mt[61]), add(mul(v[2], m[62], mt[62]), mul(v[3], m[63], mt[63]))));

	v[0] = load2(&psi[I + d2]);
	v[1] = load2(&psi[I + d0 + d2]);
	v[2] = load2(&psi[I + d1 + d2]);
	v[3] = load2(&psi[I + d0 + d1 + d2]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[64], mt[64]), add(mul(v[1], m[65], mt[65]), add(mul(v[2], m[66], mt[66]), mul(v[3], m[67], mt[67])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[68], mt[68]), add(mul(v[1], m[69], mt[69]), add(mul(v[2], m[70], mt[70]), mul(v[3], m[71], mt[71])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[72], mt[72]), add(mul(v[1], m[73], mt[73]), add(mul(v[2], m[74], mt[74]), mul(v[3], m[75], mt[75])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[76], mt[76]), add(mul(v[1], m[77], mt[77]), add(mul(v[2], m[78], mt[78]), mul(v[3], m[79], mt[79])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[80], mt[80]), add(mul(v[1], m[81], mt[81]), add(mul(v[2], m[82], mt[82]), mul(v[3], m[83], mt[83])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[84], mt[84]), add(mul(v[1], m[85], mt[85]), add(mul(v[2], m[86], mt[86]), mul(v[3], m[87], mt[87])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[88], mt[88]), add(mul(v[1], m[89], mt[89]), add(mul(v[2], m[90], mt[90]), mul(v[3], m[91], mt[91])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[92], mt[92]), add(mul(v[1], m[93], mt[93]), add(mul(v[2], m[94], mt[94]), mul(v[3], m[95], mt[95])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[96], mt[96]), add(mul(v[1], m[97], mt[97]), add(mul(v[2], m[98], mt[98]), mul(v[3], m[99], mt[99])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[100], mt[100]), add(mul(v[1], m[101], mt[101]), add(mul(v[2], m[102], mt[102]), mul(v[3], m[103], mt[103])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[104], mt[104]), add(mul(v[1], m[105], mt[105]), add(mul(v[2], m[106], mt[106]), mul(v[3], m[107], mt[107])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[108], mt[108]), add(mul(v[1], m[109], mt[109]), add(mul(v[2], m[110], mt[110]), mul(v[3], m[111], mt[111])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[112], mt[112]), add(mul(v[1], m[113], mt[113]), add(mul(v[2], m[114], mt[114]), mul(v[3], m[115], mt[115])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[116], mt[116]), add(mul(v[1], m[117], mt[117]), add(mul(v[2], m[118], mt[118]), mul(v[3], m[119], mt[119])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[120], mt[120]), add(mul(v[1], m[121], mt[121]), add(mul(v[2], m[122], mt[122]), mul(v[3], m[123], mt[123])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[124], mt[124]), add(mul(v[1], m[125], mt[125]), add(mul(v[2], m[126], mt[126]), mul(v[3], m[127], mt[127])))));

	v[0] = load2(&psi[I + d3]);
	v[1] = load2(&psi[I + d0 + d3]);
	v[2] = load2(&psi[I + d1 + d3]);
	v[3] = load2(&psi[I + d0 + d1 + d3]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[128], mt[128]), add(mul(v[1], m[129], mt[129]), add(mul(v[2], m[130], mt[130]), mul(v[3], m[131], mt[131])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[132], mt[132]), add(mul(v[1], m[133], mt[133]), add(mul(v[2], m[134], mt[134]), mul(v[3], m[135], mt[135])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[136], mt[136]), add(mul(v[1], m[137], mt[137]), add(mul(v[2], m[138], mt[138]), mul(v[3], m[139], mt[139])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[140], mt[140]), add(mul(v[1], m[141], mt[141]), add(mul(v[2], m[142], mt[142]), mul(v[3], m[143], mt[143])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[144], mt[144]), add(mul(v[1], m[145], mt[145]), add(mul(v[2], m[146], mt[146]), mul(v[3], m[147], mt[147])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[148], mt[148]), add(mul(v[1], m[149], mt[149]), add(mul(v[2], m[150], mt[150]), mul(v[3], m[151], mt[151])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[152], mt[152]), add(mul(v[1], m[153], mt[153]), add(mul(v[2], m[154], mt[154]), mul(v[3], m[155], mt[155])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[156], mt[156]), add(mul(v[1], m[157], mt[157]), add(mul(v[2], m[158], mt[158]), mul(v[3], m[159], mt[159])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[160], mt[160]), add(mul(v[1], m[161], mt[161]), add(mul(v[2], m[162], mt[162]), mul(v[3], m[163], mt[163])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[164], mt[164]), add(mul(v[1], m[165], mt[165]), add(mul(v[2], m[166], mt[166]), mul(v[3], m[167], mt[167])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[168], mt[168]), add(mul(v[1], m[169], mt[169]), add(mul(v[2], m[170], mt[170]), mul(v[3], m[171], mt[171])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[172], mt[172]), add(mul(v[1], m[173], mt[173]), add(mul(v[2], m[174], mt[174]), mul(v[3], m[175], mt[175])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[176], mt[176]), add(mul(v[1], m[177], mt[177]), add(mul(v[2], m[178], mt[178]), mul(v[3], m[179], mt[179])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[180], mt[180]), add(mul(v[1], m[181], mt[181]), add(mul(v[2], m[182], mt[182]), mul(v[3], m[183], mt[183])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[184], mt[184]), add(mul(v[1], m[185], mt[185]), add(mul(v[2], m[186], mt[186]), mul(v[3], m[187], mt[187])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[188], mt[188]), add(mul(v[1], m[189], mt[189]), add(mul(v[2], m[190], mt[190]), mul(v[3], m[191], mt[191])))));

	v[0] = load2(&psi[I + d2 + d3]);
	v[1] = load2(&psi[I + d0 + d2 + d3]);
	v[2] = load2(&psi[I + d1 + d2 + d3]);
	v[3] = load2(&psi[I + d0 + d1 + d2 + d3]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[192], mt[192]), add(mul(v[1], m[193], mt[193]), add(mul(v[2], m[194], mt[194]), mul(v[3], m[195], mt[195])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[196], mt[196]), add(mul(v[1], m[197], mt[197]), add(mul(v[2], m[198], mt[198]), mul(v[3], m[199], mt[199])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[200], mt[200]), add(mul(v[1], m[201], mt[201]), add(mul(v[2], m[202], mt[202]), mul(v[3], m[203], mt[203])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[204], mt[204]), add(mul(v[1], m[205], mt[205]), add(mul(v[2], m[206], mt[206]), mul(v[3], m[207], mt[207])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[208], mt[208]), add(mul(v[1], m[209], mt[209]), add(mul(v[2], m[210], mt[210]), mul(v[3], m[211], mt[211])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[212], mt[212]), add(mul(v[1], m[213], mt[213]), add(mul(v[2], m[214], mt[214]), mul(v[3], m[215], mt[215])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[216], mt[216]), add(mul(v[1], m[217], mt[217]), add(mul(v[2], m[218], mt[218]), mul(v[3], m[219], mt[219])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[220], mt[220]), add(mul(v[1], m[221], mt[221]), add(mul(v[2], m[222], mt[222]), mul(v[3], m[223], mt[223])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[224], mt[224]), add(mul(v[1], m[225], mt[225]), add(mul(v[2], m[226], mt[226]), mul(v[3], m[227], mt[227])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[228], mt[228]), add(mul(v[1], m[229], mt[229]), add(mul(v[2], m[230], mt[230]), mul(v[3], m[231], mt[231])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[232], mt[232]), add(mul(v[1], m[233], mt[233]), add(mul(v[2], m[234], mt[234]), mul(v[3], m[235], mt[235])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[236], mt[236]), add(mul(v[1], m[237], mt[237]), add(mul(v[2], m[238], mt[238]), mul(v[3], m[239], mt[239])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[240], mt[240]), add(mul(v[1], m[241], mt[241]), add(mul(v[2], m[242], mt[242]), mul(v[3], m[243], mt[243])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[244], mt[244]), add(mul(v[1], m[245], mt[245]), add(mul(v[2], m[246], mt[246]), mul(v[3], m[247], mt[247])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[248], mt[248]), add(mul(v[1], m[249], mt[249]), add(mul(v[2], m[250], mt[250]), mul(v[3], m[251], mt[251])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[252], mt[252]), add(mul(v[1], m[253], mt[253]), add(mul(v[2], m[254], mt[254]), mul(v[3], m[255], mt[255])))));

	v[0] = load2(&psi[I + d4]);
	v[1] = load2(&psi[I + d0 + d4]);
	v[2] = load2(&psi[I + d1 + d4]);
	v[3] = load2(&psi[I + d0 + d1 + d4]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[256], mt[256]), add(mul(v[1], m[257], mt[257]), add(mul(v[2], m[258], mt[258]), mul(v[3], m[259], mt[259])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[260], mt[260]), add(mul(v[1], m[261], mt[261]), add(mul(v[2], m[262], mt[262]), mul(v[3], m[263], mt[263])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[264], mt[264]), add(mul(v[1], m[265], mt[265]), add(mul(v[2], m[266], mt[266]), mul(v[3], m[267], mt[267])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[268], mt[268]), add(mul(v[1], m[269], mt[269]), add(mul(v[2], m[270], mt[270]), mul(v[3], m[271], mt[271])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[272], mt[272]), add(mul(v[1], m[273], mt[273]), add(mul(v[2], m[274], mt[274]), mul(v[3], m[275], mt[275])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[276], mt[276]), add(mul(v[1], m[277], mt[277]), add(mul(v[2], m[278], mt[278]), mul(v[3], m[279], mt[279])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[280], mt[280]), add(mul(v[1], m[281], mt[281]), add(mul(v[2], m[282], mt[282]), mul(v[3], m[283], mt[283])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[284], mt[284]), add(mul(v[1], m[285], mt[285]), add(mul(v[2], m[286], mt[286]), mul(v[3], m[287], mt[287])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[288], mt[288]), add(mul(v[1], m[289], mt[289]), add(mul(v[2], m[290], mt[290]), mul(v[3], m[291], mt[291])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[292], mt[292]), add(mul(v[1], m[293], mt[293]), add(mul(v[2], m[294], mt[294]), mul(v[3], m[295], mt[295])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[296], mt[296]), add(mul(v[1], m[297], mt[297]), add(mul(v[2], m[298], mt[298]), mul(v[3], m[299], mt[299])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[300], mt[300]), add(mul(v[1], m[301], mt[301]), add(mul(v[2], m[302], mt[302]), mul(v[3], m[303], mt[303])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[304], mt[304]), add(mul(v[1], m[305], mt[305]), add(mul(v[2], m[306], mt[306]), mul(v[3], m[307], mt[307])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[308], mt[308]), add(mul(v[1], m[309], mt[309]), add(mul(v[2], m[310], mt[310]), mul(v[3], m[311], mt[311])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[312], mt[312]), add(mul(v[1], m[313], mt[313]), add(mul(v[2], m[314], mt[314]), mul(v[3], m[315], mt[315])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[316], mt[316]), add(mul(v[1], m[317], mt[317]), add(mul(v[2], m[318], mt[318]), mul(v[3], m[319], mt[319])))));

	v[0] = load2(&psi[I + d2 + d4]);
	v[1] = load2(&psi[I + d0 + d2 + d4]);
	v[2] = load2(&psi[I + d1 + d2 + d4]);
	v[3] = load2(&psi[I + d0 + d1 + d2 + d4]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[320], mt[320]), add(mul(v[1], m[321], mt[321]), add(mul(v[2], m[322], mt[322]), mul(v[3], m[323], mt[323])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[324], mt[324]), add(mul(v[1], m[325], mt[325]), add(mul(v[2], m[326], mt[326]), mul(v[3], m[327], mt[327])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[328], mt[328]), add(mul(v[1], m[329], mt[329]), add(mul(v[2], m[330], mt[330]), mul(v[3], m[331], mt[331])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[332], mt[332]), add(mul(v[1], m[333], mt[333]), add(mul(v[2], m[334], mt[334]), mul(v[3], m[335], mt[335])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[336], mt[336]), add(mul(v[1], m[337], mt[337]), add(mul(v[2], m[338], mt[338]), mul(v[3], m[339], mt[339])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[340], mt[340]), add(mul(v[1], m[341], mt[341]), add(mul(v[2], m[342], mt[342]), mul(v[3], m[343], mt[343])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[344], mt[344]), add(mul(v[1], m[345], mt[345]), add(mul(v[2], m[346], mt[346]), mul(v[3], m[347], mt[347])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[348], mt[348]), add(mul(v[1], m[349], mt[349]), add(mul(v[2], m[350], mt[350]), mul(v[3], m[351], mt[351])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[352], mt[352]), add(mul(v[1], m[353], mt[353]), add(mul(v[2], m[354], mt[354]), mul(v[3], m[355], mt[355])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[356], mt[356]), add(mul(v[1], m[357], mt[357]), add(mul(v[2], m[358], mt[358]), mul(v[3], m[359], mt[359])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[360], mt[360]), add(mul(v[1], m[361], mt[361]), add(mul(v[2], m[362], mt[362]), mul(v[3], m[363], mt[363])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[364], mt[364]), add(mul(v[1], m[365], mt[365]), add(mul(v[2], m[366], mt[366]), mul(v[3], m[367], mt[367])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[368], mt[368]), add(mul(v[1], m[369], mt[369]), add(mul(v[2], m[370], mt[370]), mul(v[3], m[371], mt[371])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[372], mt[372]), add(mul(v[1], m[373], mt[373]), add(mul(v[2], m[374], mt[374]), mul(v[3], m[375], mt[375])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[376], mt[376]), add(mul(v[1], m[377], mt[377]), add(mul(v[2], m[378], mt[378]), mul(v[3], m[379], mt[379])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[380], mt[380]), add(mul(v[1], m[381], mt[381]), add(mul(v[2], m[382], mt[382]), mul(v[3], m[383], mt[383])))));

	v[0] = load2(&psi[I + d3 + d4]);
	v[1] = load2(&psi[I + d0 + d3 + d4]);
	v[2] = load2(&psi[I + d1 + d3 + d4]);
	v[3] = load2(&psi[I + d0 + d1 + d3 + d4]);

	tmp[0] = add(tmp[0], add(mul(v[0], m[384], mt[384]), add(mul(v[1], m[385], mt[385]), add(mul(v[2], m[386], mt[386]), mul(v[3], m[387], mt[387])))));
	tmp[1] = add(tmp[1], add(mul(v[0], m[388], mt[388]), add(mul(v[1], m[389], mt[389]), add(mul(v[2], m[390], mt[390]), mul(v[3], m[391], mt[391])))));
	tmp[2] = add(tmp[2], add(mul(v[0], m[392], mt[392]), add(mul(v[1], m[393], mt[393]), add(mul(v[2], m[394], mt[394]), mul(v[3], m[395], mt[395])))));
	tmp[3] = add(tmp[3], add(mul(v[0], m[396], mt[396]), add(mul(v[1], m[397], mt[397]), add(mul(v[2], m[398], mt[398]), mul(v[3], m[399], mt[399])))));
	tmp[4] = add(tmp[4], add(mul(v[0], m[400], mt[400]), add(mul(v[1], m[401], mt[401]), add(mul(v[2], m[402], mt[402]), mul(v[3], m[403], mt[403])))));
	tmp[5] = add(tmp[5], add(mul(v[0], m[404], mt[404]), add(mul(v[1], m[405], mt[405]), add(mul(v[2], m[406], mt[406]), mul(v[3], m[407], mt[407])))));
	tmp[6] = add(tmp[6], add(mul(v[0], m[408], mt[408]), add(mul(v[1], m[409], mt[409]), add(mul(v[2], m[410], mt[410]), mul(v[3], m[411], mt[411])))));
	tmp[7] = add(tmp[7], add(mul(v[0], m[412], mt[412]), add(mul(v[1], m[413], mt[413]), add(mul(v[2], m[414], mt[414]), mul(v[3], m[415], mt[415])))));
	tmp[8] = add(tmp[8], add(mul(v[0], m[416], mt[416]), add(mul(v[1], m[417], mt[417]), add(mul(v[2], m[418], mt[418]), mul(v[3], m[419], mt[419])))));
	tmp[9] = add(tmp[9], add(mul(v[0], m[420], mt[420]), add(mul(v[1], m[421], mt[421]), add(mul(v[2], m[422], mt[422]), mul(v[3], m[423], mt[423])))));
	tmp[10] = add(tmp[10], add(mul(v[0], m[424], mt[424]), add(mul(v[1], m[425], mt[425]), add(mul(v[2], m[426], mt[426]), mul(v[3], m[427], mt[427])))));
	tmp[11] = add(tmp[11], add(mul(v[0], m[428], mt[428]), add(mul(v[1], m[429], mt[429]), add(mul(v[2], m[430], mt[430]), mul(v[3], m[431], mt[431])))));
	tmp[12] = add(tmp[12], add(mul(v[0], m[432], mt[432]), add(mul(v[1], m[433], mt[433]), add(mul(v[2], m[434], mt[434]), mul(v[3], m[435], mt[435])))));
	tmp[13] = add(tmp[13], add(mul(v[0], m[436], mt[436]), add(mul(v[1], m[437], mt[437]), add(mul(v[2], m[438], mt[438]), mul(v[3], m[439], mt[439])))));
	tmp[14] = add(tmp[14], add(mul(v[0], m[440], mt[440]), add(mul(v[1], m[441], mt[441]), add(mul(v[2], m[442], mt[442]), mul(v[3], m[443], mt[443])))));
	tmp[15] = add(tmp[15], add(mul(v[0], m[444], mt[444]), add(mul(v[1], m[445], mt[445]), add(mul(v[2], m[446], mt[446]), mul(v[3], m[447], mt[447])))));

	v[0] = load2(&psi[I + d2 + d3 + d4]);
	v[1] = load2(&psi[I + d0 + d2 + d3 + d4]);
	v[2] = load2(&psi[I + d1 + d2 + d3 + d4]);
	v[3] = load2(&psi[I + d0 + d1 + d2 + d3 + d4]);

	_mm256_storeu2_m128d((double*)&psi[I + d0], (double*)&psi[I], add(tmp[0], add(mul(v[0], m[448], mt[448]), add(mul(v[1], m[449], mt[449]), add(mul(v[2], m[450], mt[450]), mul(v[3], m[451], mt[451]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1], (double*)&psi[I + d1], add(tmp[1], add(mul(v[0], m[452], mt[452]), add(mul(v[1], m[453], mt[453]), add(mul(v[2], m[454], mt[454]), mul(v[3], m[455], mt[455]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d2], (double*)&psi[I + d2], add(tmp[2], add(mul(v[0], m[456], mt[456]), add(mul(v[1], m[457], mt[457]), add(mul(v[2], m[458], mt[458]), mul(v[3], m[459], mt[459]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2], (double*)&psi[I + d1 + d2], add(tmp[3], add(mul(v[0], m[460], mt[460]), add(mul(v[1], m[461], mt[461]), add(mul(v[2], m[462], mt[462]), mul(v[3], m[463], mt[463]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d3], (double*)&psi[I + d3], add(tmp[4], add(mul(v[0], m[464], mt[464]), add(mul(v[1], m[465], mt[465]), add(mul(v[2], m[466], mt[466]), mul(v[3], m[467], mt[467]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d3], (double*)&psi[I + d1 + d3], add(tmp[5], add(mul(v[0], m[468], mt[468]), add(mul(v[1], m[469], mt[469]), add(mul(v[2], m[470], mt[470]), mul(v[3], m[471], mt[471]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d2 + d3], (double*)&psi[I + d2 + d3], add(tmp[6], add(mul(v[0], m[472], mt[472]), add(mul(v[1], m[473], mt[473]), add(mul(v[2], m[474], mt[474]), mul(v[3], m[475], mt[475]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2 + d3], (double*)&psi[I + d1 + d2 + d3], add(tmp[7], add(mul(v[0], m[476], mt[476]), add(mul(v[1], m[477], mt[477]), add(mul(v[2], m[478], mt[478]), mul(v[3], m[479], mt[479]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d4], (double*)&psi[I + d4], add(tmp[8], add(mul(v[0], m[480], mt[480]), add(mul(v[1], m[481], mt[481]), add(mul(v[2], m[482], mt[482]), mul(v[3], m[483], mt[483]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d4], (double*)&psi[I + d1 + d4], add(tmp[9], add(mul(v[0], m[484], mt[484]), add(mul(v[1], m[485], mt[485]), add(mul(v[2], m[486], mt[486]), mul(v[3], m[487], mt[487]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d2 + d4], (double*)&psi[I + d2 + d4], add(tmp[10], add(mul(v[0], m[488], mt[488]), add(mul(v[1], m[489], mt[489]), add(mul(v[2], m[490], mt[490]), mul(v[3], m[491], mt[491]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2 + d4], (double*)&psi[I + d1 + d2 + d4], add(tmp[11], add(mul(v[0], m[492], mt[492]), add(mul(v[1], m[493], mt[493]), add(mul(v[2], m[494], mt[494]), mul(v[3], m[495], mt[495]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d3 + d4], (double*)&psi[I + d3 + d4], add(tmp[12], add(mul(v[0], m[496], mt[496]), add(mul(v[1], m[497], mt[497]), add(mul(v[2], m[498], mt[498]), mul(v[3], m[499], mt[499]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d3 + d4], (double*)&psi[I + d1 + d3 + d4], add(tmp[13], add(mul(v[0], m[500], mt[500]), add(mul(v[1], m[501], mt[501]), add(mul(v[2], m[502], mt[502]), mul(v[3], m[503], mt[503]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d2 + d3 + d4], (double*)&psi[I + d2 + d3 + d4], add(tmp[14], add(mul(v[0], m[504], mt[504]), add(mul(v[1], m[505], mt[505]), add(mul(v[2], m[506], mt[506]), mul(v[3], m[507], mt[507]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2 + d3 + d4], (double*)&psi[I + d1 + d2 + d3 + d4], add(tmp[15], add(mul(v[0], m[508], mt[508]), add(mul(v[1], m[509], mt[509]), add(mul(v[2], m[510], mt[510]), mul(v[3], m[511], mt[511]))))));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id4, unsigned id3, unsigned id2, unsigned id1, unsigned id0, M const& m, std::size_t ctrlmask)
{
	std::size_t n = psi.size();
	std::size_t d0 = 1UL << id0;
	std::size_t d1 = 1UL << id1;
	std::size_t d2 = 1UL << id2;
	std::size_t d3 = 1UL << id3;
	std::size_t d4 = 1UL << id4;

	__m256d mm[] = {load(&m[0][0], &m[1][0]), load(&m[0][1], &m[1][1]), load(&m[0][2], &m[1][2]), load(&m[0][3], &m[1][3]), load(&m[2][0], &m[3][0]), load(&m[2][1], &m[3][1]), load(&m[2][2], &m[3][2]), load(&m[2][3], &m[3][3]), load(&m[4][0], &m[5][0]), load(&m[4][1], &m[5][1]), load(&m[4][2], &m[5][2]), load(&m[4][3], &m[5][3]), load(&m[6][0], &m[7][0]), load(&m[6][1], &m[7][1]), load(&m[6][2], &m[7][2]), load(&m[6][3], &m[7][3]), load(&m[8][0], &m[9][0]), load(&m[8][1], &m[9][1]), load(&m[8][2], &m[9][2]), load(&m[8][3], &m[9][3]), load(&m[10][0], &m[11][0]), load(&m[10][1], &m[11][1]), load(&m[10][2], &m[11][2]), load(&m[10][3], &m[11][3]), load(&m[12][0], &m[13][0]), load(&m[12][1], &m[13][1]), load(&m[12][2], &m[13][2]), load(&m[12][3], &m[13][3]), load(&m[14][0], &m[15][0]), load(&m[14][1], &m[15][1]), load(&m[14][2], &m[15][2]), load(&m[14][3], &m[15][3]), load(&m[16][0], &m[17][0]), load(&m[16][1], &m[17][1]), load(&m[16][2], &m[17][2]), load(&m[16][3], &m[17][3]), load(&m[18][0], &m[19][0]), load(&m[18][1], &m[19][1]), load(&m[18][2], &m[19][2]), load(&m[18][3], &m[19][3]), load(&m[20][0], &m[21][0]), load(&m[20][1], &m[21][1]), load(&m[20][2], &m[21][2]), load(&m[20][3], &m[21][3]), load(&m[22][0], &m[23][0]), load(&m[22][1], &m[23][1]), load(&m[22][2], &m[23][2]), load(&m[22][3], &m[23][3]), load(&m[24][0], &m[25][0]), load(&m[24][1], &m[25][1]), load(&m[24][2], &m[25][2]), load(&m[24][3], &m[25][3]), load(&m[26][0], &m[27][0]), load(&m[26][1], &m[27][1]), load(&m[26][2], &m[27][2]), load(&m[26][3], &m[27][3]), load(&m[28][0], &m[29][0]), load(&m[28][1], &m[29][1]), load(&m[28][2], &m[29][2]), load(&m[28][3], &m[29][3]), load(&m[30][0], &m[31][0]), load(&m[30][1], &m[31][1]), load(&m[30][2], &m[31][2]), load(&m[30][3], &m[31][3]), load(&m[0][4], &m[1][4]), load(&m[0][5], &m[1][5]), load(&m[0][6], &m[1][6]), load(&m[0][7], &m[1][7]), load(&m[2][4], &m[3][4]), load(&m[2][5], &m[3][5]), load(&m[2][6], &m[3][6]), load(&m[2][7], &m[3][7]), load(&m[4][4], &m[5][4]), load(&m[4][5], &m[5][5]), load(&m[4][6], &m[5][6]), load(&m[4][7], &m[5][7]), load(&m[6][4], &m[7][4]), load(&m[6][5], &m[7][5]), load(&m[6][6], &m[7][6]), load(&m[6][7], &m[7][7]), load(&m[8][4], &m[9][4]), load(&m[8][5], &m[9][5]), load(&m[8][6], &m[9][6]), load(&m[8][7], &m[9][7]), load(&m[10][4], &m[11][4]), load(&m[10][5], &m[11][5]), load(&m[10][6], &m[11][6]), load(&m[10][7], &m[11][7]), load(&m[12][4], &m[13][4]), load(&m[12][5], &m[13][5]), load(&m[12][6], &m[13][6]), load(&m[12][7], &m[13][7]), load(&m[14][4], &m[15][4]), load(&m[14][5], &m[15][5]), load(&m[14][6], &m[15][6]), load(&m[14][7], &m[15][7]), load(&m[16][4], &m[17][4]), load(&m[16][5], &m[17][5]), load(&m[16][6], &m[17][6]), load(&m[16][7], &m[17][7]), load(&m[18][4], &m[19][4]), load(&m[18][5], &m[19][5]), load(&m[18][6], &m[19][6]), load(&m[18][7], &m[19][7]), load(&m[20][4], &m[21][4]), load(&m[20][5], &m[21][5]), load(&m[20][6], &m[21][6]), load(&m[20][7], &m[21][7]), load(&m[22][4], &m[23][4]), load(&m[22][5], &m[23][5]), load(&m[22][6], &m[23][6]), load(&m[22][7], &m[23][7]), load(&m[24][4], &m[25][4]), load(&m[24][5], &m[25][5]), load(&m[24][6], &m[25][6]), load(&m[24][7], &m[25][7]), load(&m[26][4], &m[27][4]), load(&m[26][5], &m[27][5]), load(&m[26][6], &m[27][6]), load(&m[26][7], &m[27][7]), load(&m[28][4], &m[29][4]), load(&m[28][5], &m[29][5]), load(&m[28][6], &m[29][6]), load(&m[28][7], &m[29][7]), load(&m[30][4], &m[31][4]), load(&m[30][5], &m[31][5]), load(&m[30][6], &m[31][6]), load(&m[30][7], &m[31][7]), load(&m[0][8], &m[1][8]), load(&m[0][9], &m[1][9]), load(&m[0][10], &m[1][10]), load(&m[0][11], &m[1][11]), load(&m[2][8], &m[3][8]), load(&m[2][9], &m[3][9]), load(&m[2][10], &m[3][10]), load(&m[2][11], &m[3][11]), load(&m[4][8], &m[5][8]), load(&m[4][9], &m[5][9]), load(&m[4][10], &m[5][10]), load(&m[4][11], &m[5][11]), load(&m[6][8], &m[7][8]), load(&m[6][9], &m[7][9]), load(&m[6][10], &m[7][10]), load(&m[6][11], &m[7][11]), load(&m[8][8], &m[9][8]), load(&m[8][9], &m[9][9]), load(&m[8][10], &m[9][10]), load(&m[8][11], &m[9][11]), load(&m[10][8], &m[11][8]), load(&m[10][9], &m[11][9]), load(&m[10][10], &m[11][10]), load(&m[10][11], &m[11][11]), load(&m[12][8], &m[13][8]), load(&m[12][9], &m[13][9]), load(&m[12][10], &m[13][10]), load(&m[12][11], &m[13][11]), load(&m[14][8], &m[15][8]), load(&m[14][9], &m[15][9]), load(&m[14][10], &m[15][10]), load(&m[14][11], &m[15][11]), load(&m[16][8], &m[17][8]), load(&m[16][9], &m[17][9]), load(&m[16][10], &m[17][10]), load(&m[16][11], &m[17][11]), load(&m[18][8], &m[19][8]), load(&m[18][9], &m[19][9]), load(&m[18][10], &m[19][10]), load(&m[18][11], &m[19][11]), load(&m[20][8], &m[21][8]), load(&m[20][9], &m[21][9]), load(&m[20][10], &m[21][10]), load(&m[20][11], &m[21][11]), load(&m[22][8], &m[23][8]), load(&m[22][9], &m[23][9]), load(&m[22][10], &m[23][10]), load(&m[22][11], &m[23][11]), load(&m[24][8], &m[25][8]), load(&m[24][9], &m[25][9]), load(&m[24][10], &m[25][10]), load(&m[24][11], &m[25][11]), load(&m[26][8], &m[27][8]), load(&m[26][9], &m[27][9]), load(&m[26][10], &m[27][10]), load(&m[26][11], &m[27][11]), load(&m[28][8], &m[29][8]), load(&m[28][9], &m[29][9]), load(&m[28][10], &m[29][10]), load(&m[28][11], &m[29][11]), load(&m[30][8], &m[31][8]), load(&m[30][9], &m[31][9]), load(&m[30][10], &m[31][10]), load(&m[30][11], &m[31][11]), load(&m[0][12], &m[1][12]), load(&m[0][13], &m[1][13]), load(&m[0][14], &m[1][14]), load(&m[0][15], &m[1][15]), load(&m[2][12], &m[3][12]), load(&m[2][13], &m[3][13]), load(&m[2][14], &m[3][14]), load(&m[2][15], &m[3][15]), load(&m[4][12], &m[5][12]), load(&m[4][13], &m[5][13]), load(&m[4][14], &m[5][14]), load(&m[4][15], &m[5][15]), load(&m[6][12], &m[7][12]), load(&m[6][13], &m[7][13]), load(&m[6][14], &m[7][14]), load(&m[6][15], &m[7][15]), load(&m[8][12], &m[9][12]), load(&m[8][13], &m[9][13]), load(&m[8][14], &m[9][14]), load(&m[8][15], &m[9][15]), load(&m[10][12], &m[11][12]), load(&m[10][13], &m[11][13]), load(&m[10][14], &m[11][14]), load(&m[10][15], &m[11][15]), load(&m[12][12], &m[13][12]), load(&m[12][13], &m[13][13]), load(&m[12][14], &m[13][14]), load(&m[12][15], &m[13][15]), load(&m[14][12], &m[15][12]), load(&m[14][13], &m[15][13]), load(&m[14][14], &m[15][14]), load(&m[14][15], &m[15][15]), load(&m[16][12], &m[17][12]), load(&m[16][13], &m[17][13]), load(&m[16][14], &m[17][14]), load(&m[16][15], &m[17][15]), load(&m[18][12], &m[19][12]), load(&m[18][13], &m[19][13]), load(&m[18][14], &m[19][14]), load(&m[18][15], &m[19][15]), load(&m[20][12], &m[21][12]), load(&m[20][13], &m[21][13]), load(&m[20][14], &m[21][14]), load(&m[20][15], &m[21][15]), load(&m[22][12], &m[23][12]), load(&m[22][13], &m[23][13]), load(&m[22][14], &m[23][14]), load(&m[22][15], &m[23][15]), load(&m[24][12], &m[25][12]), load(&m[24][13], &m[25][13]), load(&m[24][14], &m[25][14]), load(&m[24][15], &m[25][15]), load(&m[26][12], &m[27][12]), load(&m[26][13], &m[27][13]), load(&m[26][14], &m[27][14]), load(&m[26][15], &m[27][15]), load(&m[28][12], &m[29][12]), load(&m[28][13], &m[29][13]), load(&m[28][14], &m[29][14]), load(&m[28][15], &m[29][15]), load(&m[30][12], &m[31][12]), load(&m[30][13], &m[31][13]), load(&m[30][14], &m[31][14]), load(&m[30][15], &m[31][15]), load(&m[0][16], &m[1][16]), load(&m[0][17], &m[1][17]), load(&m[0][18], &m[1][18]), load(&m[0][19], &m[1][19]), load(&m[2][16], &m[3][16]), load(&m[2][17], &m[3][17]), load(&m[2][18], &m[3][18]), load(&m[2][19], &m[3][19]), load(&m[4][16], &m[5][16]), load(&m[4][17], &m[5][17]), load(&m[4][18], &m[5][18]), load(&m[4][19], &m[5][19]), load(&m[6][16], &m[7][16]), load(&m[6][17], &m[7][17]), load(&m[6][18], &m[7][18]), load(&m[6][19], &m[7][19]), load(&m[8][16], &m[9][16]), load(&m[8][17], &m[9][17]), load(&m[8][18], &m[9][18]), load(&m[8][19], &m[9][19]), load(&m[10][16], &m[11][16]), load(&m[10][17], &m[11][17]), load(&m[10][18], &m[11][18]), load(&m[10][19], &m[11][19]), load(&m[12][16], &m[13][16]), load(&m[12][17], &m[13][17]), load(&m[12][18], &m[13][18]), load(&m[12][19], &m[13][19]), load(&m[14][16], &m[15][16]), load(&m[14][17], &m[15][17]), load(&m[14][18], &m[15][18]), load(&m[14][19], &m[15][19]), load(&m[16][16], &m[17][16]), load(&m[16][17], &m[17][17]), load(&m[16][18], &m[17][18]), load(&m[16][19], &m[17][19]), load(&m[18][16], &m[19][16]), load(&m[18][17], &m[19][17]), load(&m[18][18], &m[19][18]), load(&m[18][19], &m[19][19]), load(&m[20][16], &m[21][16]), load(&m[20][17], &m[21][17]), load(&m[20][18], &m[21][18]), load(&m[20][19], &m[21][19]), load(&m[22][16], &m[23][16]), load(&m[22][17], &m[23][17]), load(&m[22][18], &m[23][18]), load(&m[22][19], &m[23][19]), load(&m[24][16], &m[25][16]), load(&m[24][17], &m[25][17]), load(&m[24][18], &m[25][18]), load(&m[24][19], &m[25][19]), load(&m[26][16], &m[27][16]), load(&m[26][17], &m[27][17]), load(&m[26][18], &m[27][18]), load(&m[26][19], &m[27][19]), load(&m[28][16], &m[29][16]), load(&m[28][17], &m[29][17]), load(&m[28][18], &m[29][18]), load(&m[28][19], &m[29][19]), load(&m[30][16], &m[31][16]), load(&m[30][17], &m[31][17]), load(&m[30][18], &m[31][18]), load(&m[30][19], &m[31][19]), load(&m[0][20], &m[1][20]), load(&m[0][21], &m[1][21]), load(&m[0][22], &m[1][22]), load(&m[0][23], &m[1][23]), load(&m[2][20], &m[3][20]), load(&m[2][21], &m[3][21]), load(&m[2][22], &m[3][22]), load(&m[2][23], &m[3][23]), load(&m[4][20], &m[5][20]), load(&m[4][21], &m[5][21]), load(&m[4][22], &m[5][22]), load(&m[4][23], &m[5][23]), load(&m[6][20], &m[7][20]), load(&m[6][21], &m[7][21]), load(&m[6][22], &m[7][22]), load(&m[6][23], &m[7][23]), load(&m[8][20], &m[9][20]), load(&m[8][21], &m[9][21]), load(&m[8][22], &m[9][22]), load(&m[8][23], &m[9][23]), load(&m[10][20], &m[11][20]), load(&m[10][21], &m[11][21]), load(&m[10][22], &m[11][22]), load(&m[10][23], &m[11][23]), load(&m[12][20], &m[13][20]), load(&m[12][21], &m[13][21]), load(&m[12][22], &m[13][22]), load(&m[12][23], &m[13][23]), load(&m[14][20], &m[15][20]), load(&m[14][21], &m[15][21]), load(&m[14][22], &m[15][22]), load(&m[14][23], &m[15][23]), load(&m[16][20], &m[17][20]), load(&m[16][21], &m[17][21]), load(&m[16][22], &m[17][22]), load(&m[16][23], &m[17][23]), load(&m[18][20], &m[19][20]), load(&m[18][21], &m[19][21]), load(&m[18][22], &m[19][22]), load(&m[18][23], &m[19][23]), load(&m[20][20], &m[21][20]), load(&m[20][21], &m[21][21]), load(&m[20][22], &m[21][22]), load(&m[20][23], &m[21][23]), load(&m[22][20], &m[23][20]), load(&m[22][21], &m[23][21]), load(&m[22][22], &m[23][22]), load(&m[22][23], &m[23][23]), load(&m[24][20], &m[25][20]), load(&m[24][21], &m[25][21]), load(&m[24][22], &m[25][22]), load(&m[24][23], &m[25][23]), load(&m[26][20], &m[27][20]), load(&m[26][21], &m[27][21]), load(&m[26][22], &m[27][22]), load(&m[26][23], &m[27][23]), load(&m[28][20], &m[29][20]), load(&m[28][21], &m[29][21]), load(&m[28][22], &m[29][22]), load(&m[28][23], &m[29][23]), load(&m[30][20], &m[31][20]), load(&m[30][21], &m[31][21]), load(&m[30][22], &m[31][22]), load(&m[30][23], &m[31][23]), load(&m[0][24], &m[1][24]), load(&m[0][25], &m[1][25]), load(&m[0][26], &m[1][26]), load(&m[0][27], &m[1][27]), load(&m[2][24], &m[3][24]), load(&m[2][25], &m[3][25]), load(&m[2][26], &m[3][26]), load(&m[2][27], &m[3][27]), load(&m[4][24], &m[5][24]), load(&m[4][25], &m[5][25]), load(&m[4][26], &m[5][26]), load(&m[4][27], &m[5][27]), load(&m[6][24], &m[7][24]), load(&m[6][25], &m[7][25]), load(&m[6][26], &m[7][26]), load(&m[6][27], &m[7][27]), load(&m[8][24], &m[9][24]), load(&m[8][25], &m[9][25]), load(&m[8][26], &m[9][26]), load(&m[8][27], &m[9][27]), load(&m[10][24], &m[11][24]), load(&m[10][25], &m[11][25]), load(&m[10][26], &m[11][26]), load(&m[10][27], &m[11][27]), load(&m[12][24], &m[13][24]), load(&m[12][25], &m[13][25]), load(&m[12][26], &m[13][26]), load(&m[12][27], &m[13][27]), load(&m[14][24], &m[15][24]), load(&m[14][25], &m[15][25]), load(&m[14][26], &m[15][26]), load(&m[14][27], &m[15][27]), load(&m[16][24], &m[17][24]), load(&m[16][25], &m[17][25]), load(&m[16][26], &m[17][26]), load(&m[16][27], &m[17][27]), load(&m[18][24], &m[19][24]), load(&m[18][25], &m[19][25]), load(&m[18][26], &m[19][26]), load(&m[18][27], &m[19][27]), load(&m[20][24], &m[21][24]), load(&m[20][25], &m[21][25]), load(&m[20][26], &m[21][26]), load(&m[20][27], &m[21][27]), load(&m[22][24], &m[23][24]), load(&m[22][25], &m[23][25]), load(&m[22][26], &m[23][26]), load(&m[22][27], &m[23][27]), load(&m[24][24], &m[25][24]), load(&m[24][25], &m[25][25]), load(&m[24][26], &m[25][26]), load(&m[24][27], &m[25][27]), load(&m[26][24], &m[27][24]), load(&m[26][25], &m[27][25]), load(&m[26][26], &m[27][26]), load(&m[26][27], &m[27][27]), load(&m[28][24], &m[29][24]), load(&m[28][25], &m[29][25]), load(&m[28][26], &m[29][26]), load(&m[28][27], &m[29][27]), load(&m[30][24], &m[31][24]), load(&m[30][25], &m[31][25]), load(&m[30][26], &m[31][26]), load(&m[30][27], &m[31][27]), load(&m[0][28], &m[1][28]), load(&m[0][29], &m[1][29]), load(&m[0][30], &m[1][30]), load(&m[0][31], &m[1][31]), load(&m[2][28], &m[3][28]), load(&m[2][29], &m[3][29]), load(&m[2][30], &m[3][30]), load(&m[2][31], &m[3][31]), load(&m[4][28], &m[5][28]), load(&m[4][29], &m[5][29]), load(&m[4][30], &m[5][30]), load(&m[4][31], &m[5][31]), load(&m[6][28], &m[7][28]), load(&m[6][29], &m[7][29]), load(&m[6][30], &m[7][30]), load(&m[6][31], &m[7][31]), load(&m[8][28], &m[9][28]), load(&m[8][29], &m[9][29]), load(&m[8][30], &m[9][30]), load(&m[8][31], &m[9][31]), load(&m[10][28], &m[11][28]), load(&m[10][29], &m[11][29]), load(&m[10][30], &m[11][30]), load(&m[10][31], &m[11][31]), load(&m[12][28], &m[13][28]), load(&m[12][29], &m[13][29]), load(&m[12][30], &m[13][30]), load(&m[12][31], &m[13][31]), load(&m[14][28], &m[15][28]), load(&m[14][29], &m[15][29]), load(&m[14][30], &m[15][30]), load(&m[14][31], &m[15][31]), load(&m[16][28], &m[17][28]), load(&m[16][29], &m[17][29]), load(&m[16][30], &m[17][30]), load(&m[16][31], &m[17][31]), load(&m[18][28], &m[19][28]), load(&m[18][29], &m[19][29]), load(&m[18][30], &m[19][30]), load(&m[18][31], &m[19][31]), load(&m[20][28], &m[21][28]), load(&m[20][29], &m[21][29]), load(&m[20][30], &m[21][30]), load(&m[20][31], &m[21][31]), load(&m[22][28], &m[23][28]), load(&m[22][29], &m[23][29]), load(&m[22][30], &m[23][30]), load(&m[22][31], &m[23][31]), load(&m[24][28], &m[25][28]), load(&m[24][29], &m[25][29]), load(&m[24][30], &m[25][30]), load(&m[24][31], &m[25][31]), load(&m[26][28], &m[27][28]), load(&m[26][29], &m[27][29]), load(&m[26][30], &m[27][30]), load(&m[26][31], &m[27][31]), load(&m[28][28], &m[29][28]), load(&m[28][29], &m[29][29]), load(&m[28][30], &m[29][30]), load(&m[28][31], &m[29][31]), load(&m[30][28], &m[31][28]), load(&m[30][29], &m[31][29]), load(&m[30][30], &m[31][30]), load(&m[30][31], &m[31][31])};
	__m256d mmt[512];

	__m256d neg = _mm256_setr_pd(1.0, -1.0, 1.0, -1.0);
	for (unsigned i = 0; i < 512; ++i){
		auto badc = _mm256_permute_pd(mm[i], 5);
		mmt[i] = _mm256_mul_pd(badc, neg);
	}

	std::size_t dsorted[] = {d0 , d1, d2, d3, d4};
	std::sort(dsorted, dsorted + 5, std::greater<std::size_t>());

	if (ctrlmask == 0){
		#pragma omp for collapse(LOOP_COLLAPSE5) schedule(static)
		for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
			for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
				for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
					for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
						for (std::size_t i4 = 0; i4 < dsorted[3]; i4 += 2 * dsorted[4]){
							for (std::size_t i5 = 0; i5 < dsorted[4]; ++i5){
								kernel_core(psi, i0 + i1 + i2 + i3 + i4 + i5, d0, d1, d2, d3, d4, mm, mmt);
							}
						}
					}
				}
			}
		}
	}
	else{
		#pragma omp for collapse(LOOP_COLLAPSE5) schedule(static)
		for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
			for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
				for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
					for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
						for (std::size_t i4 = 0; i4 < dsorted[3]; i4 += 2 * dsorted[4]){
							for (std::size_t i5 = 0; i5 < dsorted[4]; ++i5){
								if (((i0 + i1 + i2 + i3 + i4 + i5)&ctrlmask) == ctrlmask)
									kernel_core(psi, i0 + i1 + i2 + i3 + i4 + i5, d0, d1, d2, d3, d4, mm, mmt);
							}
						}
					}
				}
			}
		}
	}
}

