package kr.co.mindone.ems.epa;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EpaMapper {
	Integer getEpaModeInfo();

	void setEpaMode(int mode);
}
