package com.wapplab.pms.repository;

import com.wapplab.pms.web.common.ScadaDto;
import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;

@Mapper
public interface CommonMapper {
	void msgInsert(HashMap<String, Object> map);

	List<HashMap<String, String>> kafkaTagList();

	void insertRawData(HashMap<String, Object> insertMap);

	void insertScadaDto(ScadaDto scadaDto);
}
