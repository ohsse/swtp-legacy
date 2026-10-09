package com.wapplab.pms.service;

import com.wapplab.pms.repository.CommonMapper;
import com.wapplab.pms.web.common.ScadaDto;
import lombok.RequiredArgsConstructor;
import org.apache.kafka.common.protocol.types.Field;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CommonService {
	@Autowired
	private final CommonMapper commonMapper;

	public void msgInsert(HashMap<String, Object> map){
		HashMap<String, Object> mapTemp = map;


		commonMapper.msgInsert(map);
	}

	public List<HashMap<String, String>> kafkaTagList(){
		return commonMapper.kafkaTagList();
	}

	public void insertRawData(HashMap<String, Object> insertMap){
		commonMapper.insertRawData(insertMap);
	}

	public void insertScadaDto(ScadaDto scadaDto){
		commonMapper.insertScadaDto(scadaDto);
	}





}
