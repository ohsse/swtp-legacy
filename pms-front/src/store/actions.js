import { reservation } from '@/api/index';

const RESERVATION_LIST = async (id) => {
    const { data } = await reservation(id);
    return data;
};

export { RESERVATION_LIST };
